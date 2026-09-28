from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from app.core.config import get_settings
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
    Orchestration service powering Phase 1B-2 & Phase 1B-4 RAG Knowledge Retrieval.
    Encapsulates query embedding generation, vector similarity search against ChromaDB,
    and distance threshold filtering for candidate relevance.
    """

    def __init__(
        self,
        embedder: Optional[SentenceTransformerEmbeddings] = None,
        vector_store: Optional[ChromaVectorStore] = None,
        distance_threshold: Optional[float] = None
    ):
        settings = get_settings()
        self.embedder = embedder or SentenceTransformerEmbeddings()
        self.vector_store = vector_store or ChromaVectorStore()
        self.distance_threshold = (
            distance_threshold
            if distance_threshold is not None
            else settings.RAG_DISTANCE_THRESHOLD
        )

    def search(
        self,
        query: str,
        top_k: int = 4,
        where_filter: Optional[Dict[str, Any]] = None,
        distance_threshold: Optional[float] = None
    ) -> RetrievalResultPayload:
        """
        Execute vector similarity search for a natural language query with distance filtering.

        Args:
            query: Natural language search string.
            top_k: Maximum number of top matching candidates to request from ChromaDB.
            where_filter: Optional metadata filtering dictionary.
            distance_threshold: Optional override for relevance distance threshold.

        Returns:
            RetrievalResultPayload containing matching chunks that pass distance threshold filtering.
        """
        clean_query = (query or "").strip()
        if not clean_query:
            raise RAGRetrievalError("Query string cannot be empty or whitespace-only.")

        if top_k <= 0:
            raise RAGRetrievalError(f"top_k must be a positive integer, got {top_k}.")

        # Enforce maximum top_k boundary to avoid retrieving entire collection
        effective_top_k = min(top_k, 50)
        effective_threshold = (
            distance_threshold
            if distance_threshold is not None
            else self.distance_threshold
        )

        logger.info(
            f"[RAG Retrieval] Searching knowledge base for query: '{clean_query}' "
            f"(top_k={effective_top_k}, distance_threshold={effective_threshold})"
        )

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

        # 3. Convert raw vector store results to application-level chunk objects and filter by distance threshold
        all_candidates_count = len(raw_results)
        retrieved_chunks: List[RetrievedChunkResult] = []

        for item in raw_results:
            raw_dist = item.get("distance", 0.0)
            try:
                dist = float(raw_dist)
            except (ValueError, TypeError):
                dist = 0.0

            if dist <= effective_threshold:
                chunk_id = str(item.get("chunk_id", ""))
                text = str(item.get("text", ""))
                metadata = item.get("metadata", {}) if isinstance(item.get("metadata"), dict) else {}
                retrieved_chunks.append(
                    RetrievedChunkResult(
                        chunk_id=chunk_id,
                        text=text,
                        metadata=metadata,
                        distance=dist
                    )
                )

        coll_name = getattr(self.vector_store, "collection_name", "knowledge_base")
        logger.info(
            f"[RAG Retrieval] Chroma returned {all_candidates_count} candidate(s) from collection '{coll_name}'. "
            f"Distance threshold = {effective_threshold}. "
            f"{len(retrieved_chunks)} candidate(s) passed relevance filtering."
        )

        return RetrievalResultPayload(
            query=clean_query,
            total_results=len(retrieved_chunks),
            results=retrieved_chunks
        )
