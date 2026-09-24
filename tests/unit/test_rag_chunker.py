import pytest
from app.rag.loader import ExtractedDocument, ExtractedPage
from app.rag.chunker import TextChunker, DocumentChunk


def test_chunker_normal_text():
    chunker = TextChunker(chunk_size=100, chunk_overlap=20)
    
    doc = ExtractedDocument(
        document_id="doc123",
        source="test.pdf",
        pages=[
            ExtractedPage(page_number=1, text="Paragraph one with detailed content for testing. " * 3),
            ExtractedPage(page_number=2, text="Paragraph two with more details on content generation. " * 3),
        ],
        total_pages=2,
        full_text="Combined text here"
    )

    chunks = chunker.chunk_document(doc)
    assert len(chunks) > 0
    for chunk in chunks:
        assert isinstance(chunk, DocumentChunk)
        assert chunk.document_id == "doc123"
        assert "source" in chunk.metadata
        assert chunk.metadata["source"] == "test.pdf"
        assert "page_number" in chunk.metadata
        assert len(chunk.text) <= 100 + 20  # Allows boundary padding


def test_chunker_short_text():
    chunker = TextChunker(chunk_size=1000, chunk_overlap=100)
    
    doc = ExtractedDocument(
        document_id="doc_short",
        source="short.pdf",
        pages=[ExtractedPage(page_number=1, text="Short text.")],
        total_pages=1,
        full_text="Short text."
    )

    chunks = chunker.chunk_document(doc)
    assert len(chunks) == 1
    assert chunks[0].text == "Short text."
    assert chunks[0].chunk_index == 0
    assert chunks[0].metadata["page_number"] == 1


def test_chunker_empty_doc():
    chunker = TextChunker(chunk_size=500, chunk_overlap=50)
    
    doc = ExtractedDocument(
        document_id="doc_empty",
        source="empty.pdf",
        pages=[],
        total_pages=0,
        full_text=""
    )

    chunks = chunker.chunk_document(doc)
    assert len(chunks) == 0


def test_chunker_invalid_params():
    with pytest.raises(ValueError):
        TextChunker(chunk_size=0, chunk_overlap=10)

    with pytest.raises(ValueError):
        TextChunker(chunk_size=100, chunk_overlap=100)
