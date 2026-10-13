import pytest
from unittest.mock import AsyncMock, patch

from app.mcp.client import SearchMCPClient
from app.search.models import SearchResponse, SearchResult, SearchType


@pytest.mark.asyncio
async def test_mcp_client_in_process_list_tools():
    client = SearchMCPClient(in_process=True)
    tools = await client.list_tools()
    assert len(tools) == 4
    tool_names = [t["name"] for t in tools]
    assert "search_web" in tool_names
    assert "search_news" in tool_names
    assert "search_trends" in tool_names
    assert "search_research_papers" in tool_names


@pytest.mark.asyncio
async def test_mcp_client_in_process_tool_calls():
    mock_dict = {
        "query": "fastapi",
        "search_type": "web",
        "results": [{"title": "FastAPI Web", "url": "https://fastapi.tiangolo.com", "result_type": "web"}],
        "total_results": 1,
        "provider": "mock"
    }

    with patch("app.mcp.client.direct_search_web", new_callable=AsyncMock) as mock_web:
        mock_web.return_value = mock_dict
        client = SearchMCPClient(in_process=True)
        
        response = await client.search_web("fastapi", limit=1)
        assert isinstance(response, SearchResponse)
        assert response.query == "fastapi"
        assert response.search_type == SearchType.WEB
        assert response.results[0].title == "FastAPI Web"
        mock_web.assert_called_once_with(query="fastapi", limit=1)
