import logging
import uvicorn
from mcp.server.mcpserver import MCPServer

from app.core.config import get_settings
from app.mcp.tools.search_tools import (
    search_web as tool_search_web,
    search_news as tool_search_news,
    search_trends as tool_search_trends,
    search_research_papers as tool_search_research_papers,
)

logger = logging.getLogger(__name__)

settings = get_settings()

# Create Search MCP Server instance
search_mcp_server = MCPServer(
    name=settings.MCP_SERVER_NAME,
    version="0.1.0"
)

# Register MCP Tools
@search_mcp_server.tool(
    name="search_web",
    description="Retrieve general web search results for a given query."
)
async def search_web(query: str, limit: int = 5) -> dict:
    """Execute web search via Search Service."""
    return await tool_search_web(query=query, limit=limit)


@search_mcp_server.tool(
    name="search_news",
    description="Retrieve recent news articles and coverage for a given query."
)
async def search_news(query: str, limit: int = 5) -> dict:
    """Execute news search via Search Service."""
    return await tool_search_news(query=query, limit=limit)


@search_mcp_server.tool(
    name="search_trends",
    description="Retrieve current trending topics and insights for a given query."
)
async def search_trends(query: str, limit: int = 5) -> dict:
    """Execute trend search via Search Service."""
    return await tool_search_trends(query=query, limit=limit)


@search_mcp_server.tool(
    name="search_research_papers",
    description="Retrieve academic research papers and literature for a given query."
)
async def search_research_papers(query: str, limit: int = 5) -> dict:
    """Execute academic research paper search via Search Service."""
    return await tool_search_research_papers(query=query, limit=limit)


def get_mcp_server() -> MCPServer:
    """Return the global Search MCP Server instance."""
    return search_mcp_server


def create_mcp_app():
    """Create Starlette/ASGI app for Streamable HTTP transport."""
    return search_mcp_server.streamable_http_app()


def run_server(host: str | None = None, port: int | None = None):
    """Run the Search MCP Server standalone via Streamable HTTP ASGI app."""
    host = host or settings.MCP_SERVER_HOST
    port = port or settings.MCP_SERVER_PORT
    app = create_mcp_app()
    logger.info(f"Starting Search MCP Server on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level=settings.LOG_LEVEL.lower())


if __name__ == "__main__":
    run_server()
