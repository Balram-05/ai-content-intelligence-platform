import pytest
from unittest.mock import MagicMock, patch
from app.rag.embeddings import SentenceTransformerEmbeddings, EmbeddingError


def test_embeddings_mocked():
    embedder = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    
    mock_model = MagicMock()
    # Mock return of 2 vectors of dimension 384
    mock_model.encode.return_value = MagicMock(tolist=lambda: [[0.1] * 384, [0.2] * 384])
    mock_model.get_sentence_embedding_dimension.return_value = 384

    with patch.object(embedder, '_get_model', return_value=mock_model):
        texts = ["Text chunk one", "Text chunk two"]
        vectors = embedder.embed_documents(texts)
        
        assert len(vectors) == 2
        assert len(vectors[0]) == 384
        assert embedder.dimension == 384


def test_embeddings_empty_texts():
    embedder = SentenceTransformerEmbeddings()
    vectors = embedder.embed_documents([])
    assert vectors == []


def test_embeddings_empty_query():
    embedder = SentenceTransformerEmbeddings()
    with pytest.raises(EmbeddingError):
        embedder.embed_query("   ")
