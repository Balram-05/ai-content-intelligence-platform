import pytest
from unittest.mock import AsyncMock, patch

from app.mcp.tools.search_tools import (
    search_web,
    search_news,
    search_trends,
    search_research_papers,
)
from app.search.exceptions import InvalidSearchRequestError
from app.search.models import SearchResponse, SearchResult, SearchType


@pytest.mark.asyncio
async def test_mcp_tools_success():
    mock_response = SearchResponse(
        query="test query",
        search_type=SearchType.WEB,
        results=[SearchResult(title="Mock Title", url="https://example.com")],
        total_results=1,
        provider="mock"
    )

    with patch("app.mcp.tools.search_tools.get_search_service") as mock_get_service:
        service_mock = AsyncMock()
        service_mock.search_web.return_value = mock_response
        service_mock.search_news.return_value = mock_response
        service_mock.search_trends.return_value = mock_response
        service_mock.search_research_papers.return_value = mock_response
        mock_get_service.return_value = service_mock

        res_web = await search_web("test query", limit=1)
        assert res_web["query"] == "test query"
        assert res_web["search_type"] == "web"
        assert len(res_web["results"]) == 1

        res_news = await search_news("test query", limit=1)
        assert res_news["query"] == "test query"

        res_trends = await search_trends("test query", limit=1)
        assert res_trends["query"] == "test query"

        res_papers = await search_research_papers("test query", limit=1)
        assert res_papers["query"] == "test query"


@pytest.mark.asyncio
async def test_mcp_tools_error_handling():
    with patch("app.mcp.tools.search_tools.get_search_service") as mock_get_service:
        service_mock = AsyncMock()
        service_mock.search_web.side_effect = InvalidSearchRequestError("Search query cannot be empty.")
        mock_get_service.return_value = service_mock

        res = await search_web("", limit=1)
        assert res["results"] == []
        assert res["total_results"] == 0
        assert res["provider"] == "error"
        assert "Search query cannot be empty" in res["error"]
