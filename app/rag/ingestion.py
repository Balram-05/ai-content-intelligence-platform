from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union, Dict, Any

from app.core.logging import logger
from app.rag.loader import PDFDocumentLoader, ExtractedDocument, PDFExtractionError
from app.rag.chunker import TextChunker, DocumentChunk, TextChunkerError
from app.rag.embeddings import SentenceTransformerEmbeddings, EmbeddingError
from app.rag.vector_store import ChromaVectorStore, VectorStoreError


class RAGIngestionError(Exception):
    """Raised when RAG ingestion pipeline fails."""
    pass


@dataclass
class IngestionResult:
    """Detailed summary payload returned after successful ingestion."""
    document_id: str
    source: str
    total_pages: int
    total_chunks: int
    collection_name: str
    status: str = "success"
    message: str = "Document ingested and indexed successfully"
    metadata: Dict[str, Any] = field(default_factory=dict)


class RAGIngestionService:
    """
    Orchestration service powering Phase 1B-1 RAG Knowledge Ingestion.
    Coordinates document extraction, text chunking, vector embedding, and ChromaDB storage.
    """

    def __init__(
        self,
        loader: Optional[PDFDocumentLoader] = None,
        chunker: Optional[TextChunker] = None,
        embedder: Optional[SentenceTransformerEmbeddings] = None,
        vector_store: Optional[ChromaVectorStore] = None
    ):
        self.loader = loader or PDFDocumentLoader()
        self.chunker = chunker or TextChunker()
        self.embedder = embedder or SentenceTransformerEmbeddings()
        self.vector_store = vector_store or ChromaVectorStore()

    def ingest_pdf_bytes(self, content_bytes: bytes, source_name: str) -> IngestionResult:
        """
        Run end-to-end ingestion on raw PDF file bytes.

        Args:
            content_bytes: Raw binary content of the PDF.
            source_name: Original filename or document identifier.

        Returns:
            IngestionResult containing status, chunk counts, document ID.
        """
        logger.info(f"[RAG Ingestion] Starting ingestion for document '{source_name}'...")

        # 1. Document Load & Text Extraction
        try:
            logger.info(f"[RAG] Loading document '{source_name}'")
            extracted_doc: ExtractedDocument = self.loader.load_pdf_bytes(content_bytes, source_name)
            logger.info(f"[RAG] Extracted text from {extracted_doc.total_pages} pages for '{source_name}'")
        except PDFExtractionError as e:
            logger.error(f"[RAG Ingestion] PDF loading error: {e}")
            raise RAGIngestionError(f"PDF Extraction failed: {e}") from e

        # 2. Text Chunking
        try:
            chunks = self.chunker.chunk_document(extracted_doc)
            logger.info(f"[RAG] Created {len(chunks)} chunks for '{source_name}'")
        except TextChunkerError as e:
            logger.error(f"[RAG Ingestion] Text chunking error: {e}")
            raise RAGIngestionError(f"Text chunking failed: {e}") from e

        if not chunks:
            raise RAGIngestionError(f"Document '{source_name}' produced zero valid text chunks.")

        # 3. Embedding Generation
        try:
            chunk_texts = [chunk.text for chunk in chunks]
            logger.info(f"[RAG] Generating embeddings for {len(chunk_texts)} chunks...")
            embeddings = self.embedder.embed_documents(chunk_texts)
            logger.info(f"[RAG] Generated embeddings successfully.")
        except EmbeddingError as e:
            logger.error(f"[RAG Ingestion] Embedding error: {e}")
            raise RAGIngestionError(f"Embedding generation failed: {e}") from e

        # 4. Store in ChromaDB Vector Store
        try:
            logger.info(f"[RAG] Storing chunks in ChromaDB collection '{self.vector_store.collection_name}'...")
            stored_count = self.vector_store.add_chunks(chunks, embeddings)
            logger.info(f"[RAG] Stored {stored_count} chunks in ChromaDB")
        except VectorStoreError as e:
            logger.error(f"[RAG Ingestion] Vector store error: {e}")
            raise RAGIngestionError(f"ChromaDB storage failed: {e}") from e

        logger.info(
            f"[RAG] Ingestion completed for '{source_name}' "
            f"(doc_id={extracted_doc.document_id[:12]}, chunks={stored_count})"
        )

        return IngestionResult(
            document_id=extracted_doc.document_id,
            source=source_name,
            total_pages=extracted_doc.total_pages,
            total_chunks=stored_count,
            collection_name=self.vector_store.collection_name,
            status="success",
            message=f"Successfully ingested '{source_name}' into knowledge base.",
            metadata={
                "source": source_name,
                "total_pages": extracted_doc.total_pages,
                "non_empty_pages": len(extracted_doc.pages),
                "total_chunks": stored_count,
                "embedding_model": self.embedder.model_name,
            }
        )

    def ingest_pdf_file(self, file_path: Union[str, Path]) -> IngestionResult:
        """
        Run end-to-end ingestion on a PDF file path.

        Args:
            file_path: Path to PDF file.

        Returns:
            IngestionResult payload.
        """
        path = Path(file_path)
        if not path.exists():
            raise RAGIngestionError(f"File not found: '{file_path}'")

        try:
            content_bytes = path.read_bytes()
            return self.ingest_pdf_bytes(content_bytes, source_name=path.name)
        except RAGIngestionError:
            raise
        except Exception as e:
            raise RAGIngestionError(f"Failed to ingest file '{file_path}': {e}") from e
