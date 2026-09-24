import pytest
from unittest.mock import MagicMock
from app.rag.loader import PDFDocumentLoader, ExtractedDocument, ExtractedPage
from app.rag.chunker import TextChunker
from app.rag.embeddings import SentenceTransformerEmbeddings
from app.rag.vector_store import ChromaVectorStore
from app.rag.ingestion import RAGIngestionService, IngestionResult, RAGIngestionError


def test_rag_ingestion_service_end_to_end(tmp_path):
    # Mock loader
    mock_loader = MagicMock(spec=PDFDocumentLoader)
    mock_loader.load_pdf_bytes.return_value = ExtractedDocument(
        document_id="hash123",
        source="sample.pdf",
        pages=[ExtractedPage(page_number=1, text="Sample text for ingestion testing.")],
        total_pages=1,
        full_text="Sample text for ingestion testing."
    )

    # Real chunker
    chunker = TextChunker(chunk_size=100, chunk_overlap=10)

    # Mock embedder
    mock_embedder = MagicMock(spec=SentenceTransformerEmbeddings)
    mock_embedder.model_name = "mock-model"
    mock_embedder.embed_documents.return_value = [[0.1] * 384]

    # Real vector store with temp path
    persist_dir = str(tmp_path / ".chroma_ingest")
    vector_store = ChromaVectorStore(persist_dir=persist_dir, collection_name="ingest_test")

    service = RAGIngestionService(
        loader=mock_loader,
        chunker=chunker,
        embedder=mock_embedder,
        vector_store=vector_store
    )

    result = service.ingest_pdf_bytes(b"dummy pdf bytes", source_name="sample.pdf")

    assert isinstance(result, IngestionResult)
    assert result.document_id == "hash123"
    assert result.source == "sample.pdf"
    assert result.total_pages == 1
    assert result.total_chunks == 1
    assert result.status == "success"
    assert vector_store.get_collection_stats()["total_chunks"] == 1


def test_rag_ingestion_service_empty_chunks_error():
    mock_loader = MagicMock(spec=PDFDocumentLoader)
    mock_loader.load_pdf_bytes.return_value = ExtractedDocument(
        document_id="empty123",
        source="empty.pdf",
        pages=[],
        total_pages=0,
        full_text=""
    )

    service = RAGIngestionService(loader=mock_loader)

    with pytest.raises(RAGIngestionError) as exc_info:
        service.ingest_pdf_bytes(b"dummy bytes", source_name="empty.pdf")
    
    assert "zero valid text chunks" in str(exc_info.value).lower()
