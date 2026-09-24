import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import pypdf

from app.core.logging import logger


class PDFExtractionError(Exception):
    """Raised when PDF loading or text extraction fails."""
    pass


@dataclass
class ExtractedPage:
    """Represents text and metadata extracted from a single PDF page."""
    page_number: int  # 1-indexed
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractedDocument:
    """Represents a fully extracted PDF document with deterministic ID."""
    document_id: str
    source: str
    pages: List[ExtractedPage]
    total_pages: int
    full_text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class PDFDocumentLoader:
    """Document loader responsible for extracting text from PDF files."""

    @staticmethod
    def _compute_hash(content_bytes: bytes) -> str:
        """Compute SHA-256 hash of file content for deterministic document ID."""
        return hashlib.sha256(content_bytes).hexdigest()

    def load_pdf_bytes(self, content_bytes: bytes, source_name: str) -> ExtractedDocument:
        """
        Extract text from raw PDF bytes.
        
        Args:
            content_bytes: Raw binary content of the PDF file.
            source_name: Name of the source file or identifier.

        Returns:
            ExtractedDocument containing page details and metadata.
        """
        if not content_bytes:
            raise PDFExtractionError(f"PDF content for '{source_name}' is empty (0 bytes).")

        try:
            import io
            stream = io.BytesIO(content_bytes)
            reader = pypdf.PdfReader(stream)
            
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception as e:
                    raise PDFExtractionError(f"PDF '{source_name}' is encrypted and could not be decrypted: {e}")

            total_pages = len(reader.pages)
            if total_pages == 0:
                raise PDFExtractionError(f"PDF '{source_name}' contains zero pages.")

            extracted_pages: List[ExtractedPage] = []
            full_text_parts: List[str] = []

            for index, page in enumerate(reader.pages, start=1):
                try:
                    page_text = page.extract_text() or ""
                    clean_text = page_text.strip()
                    
                    page_metadata = {
                        "source": source_name,
                        "page_number": index,
                        "total_pages": total_pages,
                    }

                    if clean_text:
                        extracted_pages.append(
                            ExtractedPage(
                                page_number=index,
                                text=clean_text,
                                metadata=page_metadata
                            )
                        )
                        full_text_parts.append(clean_text)
                except Exception as page_err:
                    logger.warning(f"Failed to extract text from page {index} of '{source_name}': {page_err}")

            combined_full_text = "\n\n".join(full_text_parts).strip()

            if not combined_full_text:
                raise PDFExtractionError(f"No readable text could be extracted from PDF '{source_name}'.")

            doc_id = self._compute_hash(content_bytes)

            logger.info(
                f"[RAG Loader] Extracted {len(extracted_pages)} non-empty pages "
                f"({total_pages} total pages) from '{source_name}' (doc_id={doc_id[:12]})"
            )

            return ExtractedDocument(
                document_id=doc_id,
                source=source_name,
                pages=extracted_pages,
                total_pages=total_pages,
                full_text=combined_full_text,
                metadata={
                    "source": source_name,
                    "total_pages": total_pages,
                    "non_empty_pages": len(extracted_pages),
                    "document_id": doc_id,
                }
            )

        except PDFExtractionError:
            raise
        except Exception as e:
            logger.error(f"[RAG Loader] Failed to load PDF '{source_name}': {e}")
            raise PDFExtractionError(f"Error extracting PDF content from '{source_name}': {e}") from e

    def load_pdf_file(self, file_path: Union[str, Path]) -> ExtractedDocument:
        """
        Extract text from a PDF file path.
        
        Args:
            file_path: Path to the PDF file on disk.

        Returns:
            ExtractedDocument containing page details and metadata.
        """
        path = Path(file_path)
        if not path.exists():
            raise PDFExtractionError(f"PDF file does not exist: '{file_path}'")
        
        if path.suffix.lower() != ".pdf":
            raise PDFExtractionError(f"Invalid file extension '{path.suffix}'. Expected '.pdf'.")

        try:
            content_bytes = path.read_bytes()
            return self.load_pdf_bytes(content_bytes, source_name=path.name)
        except PDFExtractionError:
            raise
        except Exception as e:
            raise PDFExtractionError(f"Failed reading file at '{file_path}': {e}") from e
