from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from app.core.logging import logger
from app.rag.embeddings import SentenceTransformerEmbeddings, EmbeddingError
from app.rag.vector_store import ChromaVectorStore, VectorStoreError


class RAGRetrievalError(Exception):
    """Raised when RAG knowledge retrieval operations fail."""
    pass


@dataclass
class RetrievedChunkResult:
    """Application-level data structure representing a single retrieved text chunk."""
    chunk_id: str
    text: str
    metadata: Dict[str, Any]
    distance: float


@dataclass
class RetrievalResultPayload:
    """Application-level payload containing query details and list of retrieved chunks."""
    query: str
    total_results: int
    results: List[RetrievedChunkResult] = field(default_factory=list)


class RAGRetrievalService:
    """
    Orchestration service powering Phase 1B-2 RAG Knowledge Retrieval.
    Encapsulates query embedding generation and vector similarity search against ChromaDB.
    """

    def __init__(
        self,
        embedder: Optional[SentenceTransformerEmbeddings] = None,
        vector_store: Optional[ChromaVectorStore] = None
    ):
        self.embedder = embedder or SentenceTransformerEmbeddings()
        self.vector_store = vector_store or ChromaVectorStore()

    def search(
        self,
        query: str,
        top_k: int = 4,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> RetrievalResultPayload:
        """
        Execute vector similarity search for a natural language query.

        Args:
            query: Natural language search string.
            top_k: Maximum number of top matching chunks to retrieve.
            where_filter: Optional metadata filtering dictionary.

        Returns:
            RetrievalResultPayload containing matching chunks, preserved metadata, and distances.
        """
        clean_query = (query or "").strip()
        if not clean_query:
            raise RAGRetrievalError("Query string cannot be empty or whitespace-only.")

        if top_k <= 0:
            raise RAGRetrievalError(f"top_k must be a positive integer, got {top_k}.")

        # Enforce maximum top_k boundary to avoid retrieving entire collection
        effective_top_k = min(top_k, 50)

        logger.info(f"[RAG Retrieval] Searching knowledge base for query: '{clean_query}' (top_k={effective_top_k})")

        # 1. Generate query vector using existing embedding component
        try:
            query_embedding = self.embedder.embed_query(clean_query)
        except EmbeddingError as e:
            logger.error(f"[RAG Retrieval] Query embedding generation failed: {e}")
            raise RAGRetrievalError(f"Failed to generate query embedding: {e}") from e
        except Exception as e:
            logger.error(f"[RAG Retrieval] Unexpected embedding error: {e}")
            raise RAGRetrievalError(f"Error during query embedding: {e}") from e

        # 2. Vector similarity search in ChromaDB
        try:
            raw_results = self.vector_store.query_similar(
                query_embedding=query_embedding,
                top_k=effective_top_k,
                where_filter=where_filter
            )
        except VectorStoreError as e:
            logger.error(f"[RAG Retrieval] Vector store search failed: {e}")
            raise RAGRetrievalError(f"ChromaDB search failed: {e}") from e
        except Exception as e:
            logger.error(f"[RAG Retrieval] Unexpected vector store error: {e}")
            raise RAGRetrievalError(f"Error querying ChromaDB: {e}") from e

        # 3. Convert raw vector store results to application-level chunk objects
        retrieved_chunks: List[RetrievedChunkResult] = []
        for item in raw_results:
            retrieved_chunks.append(
                RetrievedChunkResult(
                    chunk_id=item.get("chunk_id", ""),
                    text=item.get("text", ""),
                    metadata=item.get("metadata", {}),
                    distance=float(item.get("distance", 0.0))
                )
            )

        coll_name = getattr(self.vector_store, "collection_name", "knowledge_base")
        logger.info(
            f"[RAG Retrieval] Found {len(retrieved_chunks)} matching chunks "
            f"in collection '{coll_name}'"
        )

        return RetrievalResultPayload(
            query=clean_query,
            total_results=len(retrieved_chunks),
            results=retrieved_chunks
        )
