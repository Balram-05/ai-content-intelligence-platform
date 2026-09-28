import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.rag.retrieval import RAGRetrievalService


def main():
    print("Testing RAG Retrieval Service against ChromaDB...")
    service = RAGRetrievalService()

    query = "What is the content strategy guide for artificial intelligence?"
    print(f"\nQuerying: '{query}'")

    result = service.search(query=query, top_k=2)

    print("\n--- RETRIEVAL RESULTS ---")
    print(f"Query: {result.query}")
    print(f"Total Results Returned: {result.total_results}")

    for idx, item in enumerate(result.results, start=1):
        print(f"\n[Result {idx}]")
        print(f"Chunk ID: {item.chunk_id}")
        print(f"Distance: {item.distance}")
        print(f"Metadata: {item.metadata}")
        print(f"Text Snippet: {item.text[:200]}")


if __name__ == "__main__":
    main()
