from typing import List, Optional
from app.core.config import get_settings
from app.core.logging import logger


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""
    pass


class SentenceTransformerEmbeddings:
    """
    Dedicated embedding component wrapping SentenceTransformers.
    Provides lazy model loading, batch processing, and clean abstraction.
    """

    _model_instance = None
    _model_name_loaded: Optional[str] = None

    def __init__(self, model_name: Optional[str] = None):
        settings = get_settings()
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME

    def _get_model(self):
        """Lazy-load and cache the SentenceTransformer model instance."""
        if (
            SentenceTransformerEmbeddings._model_instance is None
            or SentenceTransformerEmbeddings._model_name_loaded != self.model_name
        ):
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"[RAG Embeddings] Loading SentenceTransformer model '{self.model_name}'...")
                SentenceTransformerEmbeddings._model_instance = SentenceTransformer(self.model_name)
                SentenceTransformerEmbeddings._model_name_loaded = self.model_name
                logger.info(f"[RAG Embeddings] Model '{self.model_name}' loaded successfully.")
            except Exception as e:
                logger.error(f"[RAG Embeddings] Failed to load SentenceTransformer model '{self.model_name}': {e}")
                raise EmbeddingError(f"Failed to initialize embedding model '{self.model_name}': {e}") from e
        
        return SentenceTransformerEmbeddings._model_instance

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embedding vectors for a list of document chunk texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of float vector lists.
        """
        if not texts:
            return []

        try:
            model = self._get_model()
            # encode returns numpy array or list of arrays
            embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
            return embeddings.tolist()
        except EmbeddingError:
            raise
        except Exception as e:
            logger.error(f"[RAG Embeddings] Error encoding batch of {len(texts)} texts: {e}")
            raise EmbeddingError(f"Error generating embeddings for document batch: {e}") from e

    def embed_query(self, text: str) -> List[float]:
        """
        Generate an embedding vector for a single query string.

        Args:
            text: Query string to embed.

        Returns:
            Embedding vector as list of floats.
        """
        if not text or not text.strip():
            raise EmbeddingError("Cannot generate query embedding for empty text.")

        try:
            embeddings = self.embed_documents([text])
            return embeddings[0]
        except Exception as e:
            logger.error(f"[RAG Embeddings] Error encoding query text: {e}")
            raise EmbeddingError(f"Error generating query embedding: {e}") from e

    @property
    def dimension(self) -> int:
        """Get vector dimension of the current embedding model."""
        try:
            model = self._get_model()
            return model.get_sentence_embedding_dimension()
        except Exception:
            return 384  # Default for all-MiniLM-L6-v2
