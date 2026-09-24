import pytest
from unittest.mock import MagicMock, patch
from app.rag.loader import PDFDocumentLoader, PDFExtractionError, ExtractedDocument


def create_sample_pdf_bytes() -> bytes:
    """Generate minimal valid PDF byte stream containing readable text."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
        b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
        b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources <</Font <</F1 5 0 R>>>> >> endobj\n"
        b"4 0 obj <</Length 55>> stream\n"
        b"BT /F1 12 Tf 100 700 Td (Hello RAG Knowledge Base Test) Tj ET\n"
        b"endstream\n"
        b"endobj\n"
        b"5 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj\n"
        b"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000246 00000 n \n0000000351 00000 n \n"
        b"trailer <</Size 6 /Root 1 0 R>>\nstartxref\n425\n%%EOF"
    )


def test_pdf_loader_valid_bytes():
    loader = PDFDocumentLoader()
    pdf_bytes = create_sample_pdf_bytes()
    doc = loader.load_pdf_bytes(pdf_bytes, source_name="sample.pdf")

    assert isinstance(doc, ExtractedDocument)
    assert doc.source == "sample.pdf"
    assert doc.total_pages == 1
    assert "Hello RAG Knowledge Base Test" in doc.full_text
    assert len(doc.document_id) == 64  # SHA-256 length


def test_pdf_loader_empty_bytes():
    loader = PDFDocumentLoader()
    with pytest.raises(PDFExtractionError) as exc_info:
        loader.load_pdf_bytes(b"", source_name="empty.pdf")
    assert "empty" in str(exc_info.value).lower()


def test_pdf_loader_corrupted_bytes():
    loader = PDFDocumentLoader()
    corrupt_bytes = b"NOT_A_VALID_PDF_FILE_HEADER"
    with pytest.raises(PDFExtractionError) as exc_info:
        loader.load_pdf_bytes(corrupt_bytes, source_name="corrupt.pdf")
    assert "error" in str(exc_info.value).lower() or "pdf" in str(exc_info.value).lower()


def test_pdf_loader_file_not_found(tmp_path):
    loader = PDFDocumentLoader()
    non_existent = tmp_path / "does_not_exist.pdf"
    with pytest.raises(PDFExtractionError) as exc_info:
        loader.load_pdf_file(non_existent)
    assert "does not exist" in str(exc_info.value).lower()


def test_pdf_loader_invalid_extension(tmp_path):
    loader = PDFDocumentLoader()
    txt_file = tmp_path / "doc.txt"
    txt_file.write_text("hello world")
    with pytest.raises(PDFExtractionError) as exc_info:
        loader.load_pdf_file(txt_file)
    assert "invalid file extension" in str(exc_info.value).lower()
