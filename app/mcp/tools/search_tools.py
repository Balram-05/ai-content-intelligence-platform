import logging
from typing import Any

from app.search.exceptions import SearchError
from app.search.models import SearchType
from app.search.service import SearchService

logger = logging.getLogger(__name__)

# Global or instance search service container
_search_service = SearchService()


def get_search_service() -> SearchService:
    return _search_service


async def search_web(query: str, limit: int = 5) -> dict[str, Any]:
    """MCP Tool: Retrieve web search results for a given query."""
    logger.info(f"MCP Tool invocation: search_web(query='{query}', limit={limit})")
    service = get_search_service()
    try:
        response = await service.search_web(query=query, limit=limit)
        return response.model_dump()
    except SearchError as e:
        logger.error(f"MCP Tool search_web failed: {e}")
        return {
            "query": query,
            "search_type": SearchType.WEB.value,
            "results": [],
            "total_results": 0,
            "provider": "error",
            "error": str(e)
        }


async def search_news(query: str, limit: int = 5) -> dict[str, Any]:
    """MCP Tool: Retrieve recent news search results for a given query."""
    logger.info(f"MCP Tool invocation: search_news(query='{query}', limit={limit})")
    service = get_search_service()
    try:
        response = await service.search_news(query=query, limit=limit)
        return response.model_dump()
    except SearchError as e:
        logger.error(f"MCP Tool search_news failed: {e}")
        return {
            "query": query,
            "search_type": SearchType.NEWS.value,
            "results": [],
            "total_results": 0,
            "provider": "error",
            "error": str(e)
        }


async def search_trends(query: str, limit: int = 5) -> dict[str, Any]:
    """MCP Tool: Retrieve trending topics and search results for a given query."""
    logger.info(f"MCP Tool invocation: search_trends(query='{query}', limit={limit})")
    service = get_search_service()
    try:
        response = await service.search_trends(query=query, limit=limit)
        return response.model_dump()
    except SearchError as e:
        logger.error(f"MCP Tool search_trends failed: {e}")
        return {
            "query": query,
            "search_type": SearchType.TRENDS.value,
            "results": [],
            "total_results": 0,
            "provider": "error",
            "error": str(e)
        }


async def search_research_papers(query: str, limit: int = 5) -> dict[str, Any]:
    """MCP Tool: Retrieve academic and research papers for a given query."""
    logger.info(f"MCP Tool invocation: search_research_papers(query='{query}', limit={limit})")
    service = get_search_service()
    try:
        response = await service.search_research_papers(query=query, limit=limit)
        return response.model_dump()
    except SearchError as e:
        logger.error(f"MCP Tool search_research_papers failed: {e}")
        return {
            "query": query,
            "search_type": SearchType.PAPERS.value,
            "results": [],
            "total_results": 0,
            "provider": "error",
            "error": str(e)
        }
