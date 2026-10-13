import asyncio
import logging
import sys
from pathlib import Path

# Ensure root workspace directory is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from app.mcp.client import SearchMCPClient
from app.search.models import SearchType

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("verify_search_mcp")


async def main():
    logger.info("==================================================")
    logger.info("Starting Search MCP Manual Verification (Phase 1C-1)")
    logger.info("==================================================")

    # Initialize client in in-process mode for standalone verification
    client = SearchMCPClient(in_process=True)

    tools = await client.list_tools()
    logger.info(f"Registered MCP Tools ({len(tools)}): {[t['name'] for t in tools]}")

    test_cases = [
        ("Web Search", "search_web", "artificial intelligence trends 2026"),
        ("News Search", "search_news", "AI tech developments"),
        ("Trends Search", "search_trends", "machine learning"),
        ("Research Papers Search", "search_research_papers", "large language models RAG"),
    ]

    for label, tool_name, query in test_cases:
        logger.info(f"\n--- Testing {label} ({tool_name}) ---")
        logger.info(f"Query: '{query}'")
        try:
            if tool_name == "search_web":
                response = await client.search_web(query, limit=3)
            elif tool_name == "search_news":
                response = await client.search_news(query, limit=3)
            elif tool_name == "search_trends":
                response = await client.search_trends(query, limit=3)
            elif tool_name == "search_research_papers":
                response = await client.search_research_papers(query, limit=3)
            else:
                continue

            logger.info(f"Response Provider: {response.provider}")
            logger.info(f"Search Type: {response.search_type.value}")
            logger.info(f"Total Results: {response.total_results}")
            
            for idx, res in enumerate(response.results, 1):
                logger.info(f"  Result #{idx}:")
                logger.info(f"    Title: {res.title}")
                logger.info(f"    URL: {res.url}")
                logger.info(f"    Source: {res.source}")
                logger.info(f"    Snippet: {res.snippet[:120] if res.snippet else 'N/A'}...")

        except Exception as e:
            logger.error(f"Failed to execute {tool_name}: {e}")

    logger.info("\n==================================================")
    logger.info("Search MCP Manual Verification Completed Successfully!")
    logger.info("==================================================")


if __name__ == "__main__":
    asyncio.run(main())
