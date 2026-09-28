import pytest
from unittest.mock import MagicMock
from app.rag.embeddings import SentenceTransformerEmbeddings, EmbeddingError
from app.rag.vector_store import ChromaVectorStore, VectorStoreError
from app.rag.retrieval import RAGRetrievalService, RAGRetrievalError, RetrievalResultPayload


def test_retrieval_success():
    mock_embedder = MagicMock(spec=SentenceTransformerEmbeddings)
    mock_embedder.embed_query.return_value = [0.1] * 384

    mock_vector_store = MagicMock(spec=ChromaVectorStore)
    mock_vector_store.collection_name = "test_collection"
    mock_vector_store.query_similar.return_value = [
        {
            "chunk_id": "doc1_page1_chunk0",
            "text": "LangGraph uses a supervisor node for conditional routing.",
            "metadata": {"document_id": "doc1", "page_number": 1, "chunk_index": 0, "source": "langgraph_doc.pdf"},
            "distance": 0.15
        },
        {
            "chunk_id": "doc1_page2_chunk1",
            "text": "Supervisor node coordinates research and strategy agents.",
            "metadata": {"document_id": "doc1", "page_number": 2, "chunk_index": 1, "source": "langgraph_doc.pdf"},
            "distance": 0.22
        }
    ]

    service = RAGRetrievalService(embedder=mock_embedder, vector_store=mock_vector_store)
    result = service.search(query="How does LangGraph use a supervisor?", top_k=2)

    assert isinstance(result, RetrievalResultPayload)
    assert result.query == "How does LangGraph use a supervisor?"
    assert result.total_results == 2
    assert result.results[0].chunk_id == "doc1_page1_chunk0"
    assert result.results[0].distance == 0.15
    assert result.results[0].metadata["page_number"] == 1
    
    mock_embedder.embed_query.assert_called_once_with("How does LangGraph use a supervisor?")
    mock_vector_store.query_similar.assert_called_once_with(
        query_embedding=[0.1] * 384,
        top_k=2,
        where_filter=None
    )


def test_retrieval_empty_query():
    service = RAGRetrievalService(
        embedder=MagicMock(spec=SentenceTransformerEmbeddings),
        vector_store=MagicMock(spec=ChromaVectorStore)
    )

    with pytest.raises(RAGRetrievalError) as exc_info:
        service.search(query="   ", top_k=4)

    assert "empty" in str(exc_info.value).lower()


def test_retrieval_invalid_top_k():
    service = RAGRetrievalService(
        embedder=MagicMock(spec=SentenceTransformerEmbeddings),
        vector_store=MagicMock(spec=ChromaVectorStore)
    )

    with pytest.raises(RAGRetrievalError) as exc_info:
        service.search(query="valid query", top_k=0)

    assert "positive integer" in str(exc_info.value).lower()


def test_retrieval_no_results():
    mock_embedder = MagicMock(spec=SentenceTransformerEmbeddings)
    mock_embedder.embed_query.return_value = [0.1] * 384

    mock_vector_store = MagicMock(spec=ChromaVectorStore)
    mock_vector_store.collection_name = "test_collection"
    mock_vector_store.query_similar.return_value = []

    service = RAGRetrievalService(embedder=mock_embedder, vector_store=mock_vector_store)
    result = service.search(query="Query with no matches", top_k=5)

    assert result.total_results == 0
    assert result.results == []


def test_retrieval_embedding_failure():
    mock_embedder = MagicMock(spec=SentenceTransformerEmbeddings)
    mock_embedder.embed_query.side_effect = EmbeddingError("Model initialization failed")

    service = RAGRetrievalService(
        embedder=mock_embedder,
        vector_store=MagicMock(spec=ChromaVectorStore)
    )

    with pytest.raises(RAGRetrievalError) as exc_info:
        service.search(query="test query")

    assert "failed to generate query embedding" in str(exc_info.value).lower()


def test_retrieval_vector_store_failure():
    mock_embedder = MagicMock(spec=SentenceTransformerEmbeddings)
    mock_embedder.embed_query.return_value = [0.1] * 384

    mock_vector_store = MagicMock(spec=ChromaVectorStore)
    mock_vector_store.query_similar.side_effect = VectorStoreError("ChromaDB collection error")

    service = RAGRetrievalService(embedder=mock_embedder, vector_store=mock_vector_store)

    with pytest.raises(RAGRetrievalError) as exc_info:
        service.search(query="test query")

    assert "chromadb search failed" in str(exc_info.value).lower()
