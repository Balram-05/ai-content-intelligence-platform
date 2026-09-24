from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from app.core.config import get_settings
from app.core.logging import logger
from app.rag.loader import ExtractedDocument, ExtractedPage


class TextChunkerError(Exception):
    """Raised when text chunking operations fail."""
    pass


@dataclass
class DocumentChunk:
    """Represents a text chunk prepared for embedding and vector storage."""
    chunk_id: str
    document_id: str
    text: str
    chunk_index: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class TextChunker:
    """
    Chunking component responsible for dividing extracted document text
    into overlapping chunks with preserved metadata.
    """

    def __init__(self, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None):
        settings = get_settings()
        self.chunk_size = chunk_size if chunk_size is not None else settings.RAG_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap if chunk_overlap is not None else settings.RAG_CHUNK_OVERLAP

        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be a positive integer.")
        if self.chunk_overlap < 0 or self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be non-negative and less than chunk_size.")

    def _split_text_with_overlap(self, text: str) -> List[str]:
        """
        Split a string into chunks of length up to `chunk_size` with `chunk_overlap`.
        Uses natural paragraph/sentence separators (\n\n, \n, space) where possible.
        """
        if not text or not text.strip():
            return []

        text = text.strip()
        if len(text) <= self.chunk_size:
            return [text]

        separators = ["\n\n", "\n", ". ", " ", ""]
        
        chunks: List[str] = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + self.chunk_size
            
            if end >= text_length:
                chunk = text[start:].strip()
                if chunk:
                    chunks.append(chunk)
                break

            # Find best separator position before `end`
            best_break = -1
            for sep in separators:
                if not sep:
                    best_break = end
                    break
                pos = text.rfind(sep, start + self.chunk_overlap, end)
                if pos != -1:
                    best_break = pos + len(sep)
                    break
            
            if best_break <= start:
                best_break = end

            chunk = text[start:best_break].strip()
            if chunk:
                chunks.append(chunk)

            # Move start forward, accounting for overlap
            next_start = best_break - self.chunk_overlap
            if next_start <= start:
                next_start = start + 1
            start = next_start

        return chunks

    def chunk_document(self, doc: ExtractedDocument) -> List[DocumentChunk]:
        """
        Divide an ExtractedDocument into DocumentChunks, preserving page numbers
        and document metadata.

        Args:
            doc: The ExtractedDocument to chunk.

        Returns:
            List of DocumentChunk instances.
        """
        if not doc.pages and not doc.full_text:
            logger.warning(f"[RAG Chunker] Document '{doc.source}' has no text to chunk.")
            return []

        chunks: List[DocumentChunk] = []
        global_chunk_index = 0

        # Chunk page-by-page to preserve accurate page_number metadata
        for page in doc.pages:
            page_text = page.text.strip()
            if not page_text:
                continue

            page_chunks = self._split_text_with_overlap(page_text)
            for page_chunk_text in page_chunks:
                chunk_id = f"{doc.document_id}_page{page.page_number}_chunk{global_chunk_index}"
                
                chunk_metadata = {
                    "document_id": doc.document_id,
                    "source": doc.source,
                    "page_number": page.page_number,
                    "total_pages": doc.total_pages,
                    "chunk_index": global_chunk_index,
                    "chunk_size": len(page_chunk_text),
                }

                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        document_id=doc.document_id,
                        text=page_chunk_text,
                        chunk_index=global_chunk_index,
                        metadata=chunk_metadata
                    )
                )
                global_chunk_index += 1

        # Fallback if page-based chunking yielded nothing but full_text is present
        if not chunks and doc.full_text.strip():
            raw_chunks = self._split_text_with_overlap(doc.full_text)
            for idx, raw_text in enumerate(raw_chunks):
                chunk_id = f"{doc.document_id}_chunk{idx}"
                chunk_metadata = {
                    "document_id": doc.document_id,
                    "source": doc.source,
                    "page_number": 1,
                    "total_pages": doc.total_pages or 1,
                    "chunk_index": idx,
                    "chunk_size": len(raw_text),
                }
                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        document_id=doc.document_id,
                        text=raw_text,
                        chunk_index=idx,
                        metadata=chunk_metadata
                    )
                )

        logger.info(
            f"[RAG Chunker] Created {len(chunks)} chunks from '{doc.source}' "
            f"(chunk_size={self.chunk_size}, overlap={self.chunk_overlap})"
        )
        return chunks
