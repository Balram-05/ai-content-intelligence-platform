import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.api.dependencies import get_rag_ingestion_service
from app.rag.ingestion import RAGIngestionService, IngestionResult, RAGIngestionError

client = TestClient(app)


def test_knowledge_ingest_endpoint_success():
    mock_service = MagicMock(spec=RAGIngestionService)
    mock_service.ingest_pdf_bytes.return_value = IngestionResult(
        document_id="sha256_test_hash",
        source="test_document.pdf",
        total_pages=2,
        total_chunks=5,
        collection_name="knowledge_base",
        status="success",
        message="Successfully ingested 'test_document.pdf' into knowledge base."
    )

    app.dependency_overrides[get_rag_ingestion_service] = lambda: mock_service

    try:
        response = client.post(
            "/api/v1/knowledge/ingest",
            files={"file": ("test_document.pdf", b"%PDF-1.4 dummy pdf bytes", "application/pdf")}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["document_id"] == "sha256_test_hash"
        assert data["data"]["total_pages"] == 2
        assert data["data"]["total_chunks"] == 5
    finally:
        app.dependency_overrides.clear()


def test_knowledge_ingest_endpoint_invalid_extension():
    response = client.post(
        "/api/v1/knowledge/ingest",
        files={"file": ("invalid_file.txt", b"Hello World", "text/plain")}
    )

    assert response.status_code == 400
    assert "Only PDF documents" in response.json()["detail"]


def test_knowledge_ingest_endpoint_empty_file():
    response = client.post(
        "/api/v1/knowledge/ingest",
        files={"file": ("empty.pdf", b"", "application/pdf")}
    )

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_knowledge_ingest_endpoint_ingestion_failure():
    mock_service = MagicMock(spec=RAGIngestionService)
    mock_service.ingest_pdf_bytes.side_effect = RAGIngestionError("Corrupted PDF stream")

    app.dependency_overrides[get_rag_ingestion_service] = lambda: mock_service

    try:
        response = client.post(
            "/api/v1/knowledge/ingest",
            files={"file": ("corrupt.pdf", b"%PDF-1.4 corrupt", "application/pdf")}
        )

        assert response.status_code == 422
        assert "Corrupted PDF stream" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_knowledge_search_endpoint_success():
    from app.api.dependencies import get_rag_retrieval_service
    from app.rag.retrieval import RAGRetrievalService, RetrievalResultPayload, RetrievedChunkResult

    mock_retrieval_service = MagicMock(spec=RAGRetrievalService)
    mock_retrieval_service.search.return_value = RetrievalResultPayload(
        query="LangGraph supervisor routing",
        total_results=1,
        results=[
            RetrievedChunkResult(
                chunk_id="chunk_101",
                text="Supervisor node performs conditional routing in LangGraph.",
                metadata={"document_id": "doc123", "page_number": 3, "chunk_index": 0},
                distance=0.12
            )
        ]
    )

    app.dependency_overrides[get_rag_retrieval_service] = lambda: mock_retrieval_service

    try:
        response = client.post(
            "/api/v1/knowledge/search",
            json={"query": "LangGraph supervisor routing", "top_k": 3}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["query"] == "LangGraph supervisor routing"
        assert data["data"]["total_results"] == 1
        assert data["data"]["results"][0]["chunk_id"] == "chunk_101"
        assert data["data"]["results"][0]["distance"] == 0.12
    finally:
        app.dependency_overrides.clear()


def test_knowledge_search_endpoint_validation_errors():
    # Empty query string
    response1 = client.post(
        "/api/v1/knowledge/search",
        json={"query": "", "top_k": 5}
    )
    assert response1.status_code == 422

    # Invalid top_k (0 or > 50)
    response2 = client.post(
        "/api/v1/knowledge/search",
        json={"query": "valid query", "top_k": 0}
    )
    assert response2.status_code == 422

