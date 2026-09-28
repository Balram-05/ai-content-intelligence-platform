from typing import Dict, Any, List
from app.workflows.state import ContentState
from app.rag.retrieval import RAGRetrievalService
from app.core.logging import logger


async def rag_retrieval_node(state: ContentState) -> Dict[str, Any]:
    """
    Phase 1B-3 RAG Retrieval Node (deterministic workflow node).
    Retrieves context chunks from knowledge base using topic query,
    updating state with retrieved_context, retrieval_metadata,
    and setting retrieval_completed flag to True.
    """
    logger.info(f"[RAG_RETRIEVAL_NODE] Executing retrieval for topic='{state.get('topic')}'")
    query = state.get("topic", "") or ""

    if not query.strip():
        logger.warning("[RAG_RETRIEVAL_NODE] Empty topic provided. Returning empty context.")
        return {
            "retrieved_context": [],
            "retrieval_metadata": [],
            "retrieval_completed": True
        }

    try:
        service = RAGRetrievalService()
        result = service.search(query=query)

        retrieved_context: List[str] = [chunk.text for chunk in result.results]
        retrieval_metadata: List[Dict[str, Any]] = [chunk.metadata for chunk in result.results]

        logger.info(f"[RAG_RETRIEVAL_NODE] Retrieval completed. Found {len(retrieved_context)} context chunks.")
        return {
            "retrieved_context": retrieved_context,
            "retrieval_metadata": retrieval_metadata,
            "retrieval_completed": True
        }
    except Exception as e:
        logger.warning(
            f"[RAG_RETRIEVAL_NODE] RAG retrieval service failed or unavailable: {e}. "
            "Continuing workflow with empty retrieved_context."
        )
        return {
            "retrieved_context": [],
            "retrieval_metadata": [],
            "retrieval_completed": True
        }
