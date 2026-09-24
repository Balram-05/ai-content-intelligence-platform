from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import get_settings
from app.core.logging import logger
from app.rag.chunker import DocumentChunk


class VectorStoreError(Exception):
    """Raised when ChromaDB operations fail."""
    pass


class ChromaVectorStore:
    """
    Dedicated ChromaDB Vector Store abstraction handling local persistence,
    chunk insertion, metadata indexing, and query operations.
    """

    def __init__(
        self,
        persist_dir: Optional[str] = None,
        collection_name: Optional[str] = None
    ):
        settings = get_settings()
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIR
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME

        # Ensure directory exists
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)

        try:
            self.client = chromadb.PersistentClient(path=self.persist_dir)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(
                f"[RAG VectorStore] Initialized ChromaDB collection '{self.collection_name}' "
                f"at path '{self.persist_dir}'"
            )
        except Exception as e:
            logger.error(f"[RAG VectorStore] Failed to initialize ChromaDB: {e}")
            raise VectorStoreError(f"ChromaDB initialization failed: {e}") from e

    def _sanitize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure metadata values conform to ChromaDB accepted types (str, int, float, bool)."""
        sanitized = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                sanitized[key] = value
            elif value is None:
                sanitized[key] = ""
            else:
                sanitized[key] = str(value)
        return sanitized

    def add_chunks(
        self,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]]
    ) -> int:
        """
        Add document chunks and their embedding vectors to ChromaDB.

        Args:
            chunks: List of DocumentChunk objects.
            embeddings: List of embedding vectors corresponding 1:1 to chunks.

        Returns:
            Number of chunks inserted/upserted.
        """
        if not chunks:
            return 0

        if len(chunks) != len(embeddings):
            raise VectorStoreError(
                f"Mismatch between number of chunks ({len(chunks)}) and embeddings ({len(embeddings)})."
            )

        try:
            ids = [chunk.chunk_id for chunk in chunks]
            documents = [chunk.text for chunk in chunks]
            metadatas = [self._sanitize_metadata(chunk.metadata) for chunk in chunks]

            # Use upsert to cleanly handle re-ingestion or updates
            self.collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )

            logger.info(
                f"[RAG VectorStore] Upserted {len(chunks)} chunks into collection '{self.collection_name}'"
            )
            return len(chunks)

        except Exception as e:
            logger.error(f"[RAG VectorStore] Failed to add chunks to ChromaDB: {e}")
            raise VectorStoreError(f"Error adding chunks to ChromaDB collection '{self.collection_name}': {e}") from e

    def get_collection_stats(self) -> Dict[str, Any]:
        """Return information about the collection."""
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "total_chunks": count,
                "persist_directory": str(self.persist_dir)
            }
        except Exception as e:
            logger.error(f"[RAG VectorStore] Failed to retrieve collection stats: {e}")
            raise VectorStoreError(f"Failed getting collection stats: {e}") from e

    def query_similar(
        self,
        query_embedding: List[float],
        top_k: int = 4,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query top-k most similar chunks for a given query embedding vector.

        Args:
            query_embedding: Embedding vector of query text.
            top_k: Number of nearest neighbors to retrieve.
            where_filter: Optional metadata filtering dictionary.

        Returns:
            List of result dictionaries containing document, metadata, distance, id.
        """
        try:
            kwargs: Dict[str, Any] = {
                "query_embeddings": [query_embedding],
                "n_results": top_k,
                "include": ["documents", "metadatas", "distances"]
            }
            if where_filter:
                kwargs["where"] = where_filter

            results = self.collection.query(**kwargs)

            formatted_results = []
            if results and results.get("ids") and results["ids"][0]:
                ids = results["ids"][0]
                documents = results.get("documents", [[]])[0]
                metadatas = results.get("metadatas", [[]])[0]
                distances = results.get("distances", [[]])[0]

                for i in range(len(ids)):
                    formatted_results.append({
                        "chunk_id": ids[i],
                        "text": documents[i] if i < len(documents) else "",
                        "metadata": metadatas[i] if i < len(metadatas) else {},
                        "distance": distances[i] if i < len(distances) else 0.0
                    })

            return formatted_results
        except Exception as e:
            logger.error(f"[RAG VectorStore] Error querying collection: {e}")
            raise VectorStoreError(f"Query operation failed: {e}") from e

    def delete_document(self, document_id: str) -> int:
        """
        Delete all chunks associated with a document_id.

        Args:
            document_id: Document ID to remove.

        Returns:
            Number of deleted items (approximate).
        """
        try:
            self.collection.delete(where={"document_id": document_id})
            logger.info(f"[RAG VectorStore] Deleted chunks for document_id='{document_id}'")
            return 1
        except Exception as e:
            logger.error(f"[RAG VectorStore] Failed deleting document '{document_id}': {e}")
            raise VectorStoreError(f"Failed to delete document '{document_id}': {e}") from e
