"""
Phase 1B-1 RAG Knowledge Ingestion Foundation package.
Provides PDF extraction, text chunking, sentence embeddings, ChromaDB vector store,
and end-to-end RAG ingestion pipeline.
"""

from app.rag.loader import PDFDocumentLoader, ExtractedDocument, ExtractedPage, PDFExtractionError
from app.rag.chunker import TextChunker, DocumentChunk, TextChunkerError
from app.rag.embeddings import SentenceTransformerEmbeddings, EmbeddingError
from app.rag.vector_store import ChromaVectorStore, VectorStoreError
from app.rag.ingestion import RAGIngestionService, IngestionResult, RAGIngestionError
from app.rag.retrieval import RAGRetrievalService, RetrievalResultPayload, RetrievedChunkResult, RAGRetrievalError

__all__ = [
    "PDFDocumentLoader",
    "ExtractedDocument",
    "ExtractedPage",
    "PDFExtractionError",
    "TextChunker",
    "DocumentChunk",
    "TextChunkerError",
    "SentenceTransformerEmbeddings",
    "EmbeddingError",
    "ChromaVectorStore",
    "VectorStoreError",
    "RAGIngestionService",
    "IngestionResult",
    "RAGIngestionError",
    "RAGRetrievalService",
    "RetrievalResultPayload",
    "RetrievedChunkResult",
    "RAGRetrievalError",
]
