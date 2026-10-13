import logging
from typing import Any

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client

from app.core.config import get_settings
from app.mcp.tools.search_tools import (
    search_web as direct_search_web,
    search_news as direct_search_news,
    search_trends as direct_search_trends,
    search_research_papers as direct_search_research_papers,
)
from app.search.models import SearchResponse

logger = logging.getLogger(__name__)


class SearchMCPClient:
    """Client for connecting to and interacting with the Search MCP Server."""

    def __init__(self, server_url: str | None = None, in_process: bool = False):
        settings = get_settings()
        self.server_url = server_url or f"http://{settings.MCP_SERVER_HOST}:{settings.MCP_SERVER_PORT}/mcp"
        self.in_process = in_process

    async def list_tools(self) -> list[dict[str, Any]]:
        """List available tools on the Search MCP Server."""
        if self.in_process:
            return [
                {"name": "search_web", "description": "Retrieve general web search results."},
                {"name": "search_news", "description": "Retrieve recent news articles."},
                {"name": "search_trends", "description": "Retrieve current trending topics."},
                {"name": "search_research_papers", "description": "Retrieve academic research papers."},
            ]

        logger.info(f"Listing MCP tools from server at {self.server_url}")
        async with streamable_http_client(self.server_url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                response = await session.list_tools()
                return [tool.model_dump() for tool in response.tools]

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Invoke a specific MCP tool by name with arguments."""
        if self.in_process:
            logger.info(f"SearchMCPClient executing tool '{tool_name}' in-process with args: {arguments}")
            if tool_name == "search_web":
                return await direct_search_web(**arguments)
            elif tool_name == "search_news":
                return await direct_search_news(**arguments)
            elif tool_name == "search_trends":
                return await direct_search_trends(**arguments)
            elif tool_name == "search_research_papers":
                return await direct_search_research_papers(**arguments)
            else:
                raise ValueError(f"Unknown MCP tool '{tool_name}' for in-process client.")

        logger.info(f"SearchMCPClient sending tool call '{tool_name}' to {self.server_url}")
        async with streamable_http_client(self.server_url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                # Unwrap MCP tool response content if present
                if hasattr(result, "content") and result.content:
                    first_content = result.content[0]
                    if hasattr(first_content, "text"):
                        import json
                        try:
                            return json.loads(first_content.text)
                        except Exception:
                            return {"raw_text": first_content.text}
                return result.model_dump() if hasattr(result, "model_dump") else str(result)

    async def search_web(self, query: str, limit: int = 5) -> SearchResponse:
        """Call search_web tool and return normalized SearchResponse."""
        res_dict = await self.call_tool("search_web", {"query": query, "limit": limit})
        return SearchResponse.model_validate(res_dict)

    async def search_news(self, query: str, limit: int = 5) -> SearchResponse:
        """Call search_news tool and return normalized SearchResponse."""
        res_dict = await self.call_tool("search_news", {"query": query, "limit": limit})
        return SearchResponse.model_validate(res_dict)

    async def search_trends(self, query: str, limit: int = 5) -> SearchResponse:
        """Call search_trends tool and return normalized SearchResponse."""
        res_dict = await self.call_tool("search_trends", {"query": query, "limit": limit})
        return SearchResponse.model_validate(res_dict)

    async def search_research_papers(self, query: str, limit: int = 5) -> SearchResponse:
        """Call search_research_papers tool and return normalized SearchResponse."""
        res_dict = await self.call_tool("search_research_papers", {"query": query, "limit": limit})
        return SearchResponse.model_validate(res_dict)


_client_instance: SearchMCPClient | None = None


def get_mcp_client(server_url: str | None = None, in_process: bool = False) -> SearchMCPClient:
    """Return a shared SearchMCPClient instance."""
    global _client_instance
    if _client_instance is None or server_url is not None or in_process:
        client = SearchMCPClient(server_url=server_url, in_process=in_process)
        if server_url is None and not in_process:
            _client_instance = client
        return client
    return _client_instance
