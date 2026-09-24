import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.rag.loader import PDFDocumentLoader
from app.rag.chunker import TextChunker
from app.rag.embeddings import SentenceTransformerEmbeddings
from app.rag.vector_store import ChromaVectorStore
from app.rag.ingestion import RAGIngestionService


def main():
    print("Testing RAG Ingestion Service...")

    # Create sample PDF bytes
    sample_pdf_bytes = (
        b"%PDF-1.4\n"
        b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
        b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
        b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources <</Font <</F1 5 0 R>>>> >> endobj\n"
        b"4 0 obj <</Length 68>> stream\n"
        b"BT /F1 12 Tf 100 700 Td (Artificial Intelligence Content Strategy Guide 2026) Tj ET\n"
        b"endstream\n"
        b"endobj\n"
        b"5 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj\n"
        b"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000259 00000 n \n0000000377 00000 n \n"
        b"trailer <</Size 6 /Root 1 0 R>>\nstartxref\n451\n%%EOF"
    )

    service = RAGIngestionService()
    result = service.ingest_pdf_bytes(sample_pdf_bytes, source_name="ai_strategy_guide.pdf")

    print("\n--- INGESTION RESULT ---")
    print(f"Document ID: {result.document_id}")
    print(f"Source: {result.source}")
    print(f"Total Pages: {result.total_pages}")
    print(f"Total Chunks: {result.total_chunks}")
    print(f"Collection Name: {result.collection_name}")
    print(f"Status: {result.status}")
    print(f"Message: {result.message}")

    # Verify vector store stats
    vs = ChromaVectorStore()
    stats = vs.get_collection_stats()
    print(f"\n--- CHROMADB STATS ---")
    print(f"Collection: {stats['collection_name']}")
    print(f"Total Chunks in Collection: {stats['total_chunks']}")
    print(f"Persist Directory: {stats['persist_directory']}")


if __name__ == "__main__":
    main()
