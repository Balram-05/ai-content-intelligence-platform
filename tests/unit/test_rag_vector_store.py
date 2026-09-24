import pytest
from app.rag.chunker import DocumentChunk
from app.rag.vector_store import ChromaVectorStore, VectorStoreError


def test_vector_store_add_and_stats(tmp_path):
    persist_dir = str(tmp_path / ".chroma_test")
    vector_store = ChromaVectorStore(persist_dir=persist_dir, collection_name="test_collection")

    chunks = [
        DocumentChunk(
            chunk_id="doc1_chunk0",
            document_id="doc1",
            text="First test chunk text content.",
            chunk_index=0,
            metadata={"document_id": "doc1", "source": "test1.pdf", "page_number": 1}
        ),
        DocumentChunk(
            chunk_id="doc1_chunk1",
            document_id="doc1",
            text="Second test chunk text content.",
            chunk_index=1,
            metadata={"document_id": "doc1", "source": "test1.pdf", "page_number": 1}
        )
    ]
    # Synthetic vectors of dimension 4
    embeddings = [
        [0.1, 0.2, 0.3, 0.4],
        [0.5, 0.6, 0.7, 0.8]
    ]

    count = vector_store.add_chunks(chunks, embeddings)
    assert count == 2

    stats = vector_store.get_collection_stats()
    assert stats["collection_name"] == "test_collection"
    assert stats["total_chunks"] == 2

    # Query
    results = vector_store.query_similar(query_embedding=[0.1, 0.2, 0.3, 0.4], top_k=2)
    assert len(results) == 2
    assert results[0]["chunk_id"] in ["doc1_chunk0", "doc1_chunk1"]


def test_vector_store_mismatch_error(tmp_path):
    persist_dir = str(tmp_path / ".chroma_test_mismatch")
    vector_store = ChromaVectorStore(persist_dir=persist_dir, collection_name="test_collection")

    chunks = [
        DocumentChunk(
            chunk_id="c1", document_id="d1", text="Text 1", chunk_index=0
        )
    ]
    embeddings = []

    with pytest.raises(VectorStoreError):
        vector_store.add_chunks(chunks, embeddings)
