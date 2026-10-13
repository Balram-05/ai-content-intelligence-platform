import asyncio
import json
from typing import Dict, Any, List, Optional
from langchain_core.messages import SystemMessage, HumanMessage

from app.workflows.state import ContentState
from app.core.config import get_settings
from app.core.llm import get_llm
from app.core.logging import logger
from app.mcp.client import SearchMCPClient, get_mcp_client
from app.search.models import SearchResponse


def _format_search_evidence(sources: List[Dict[str, Any]]) -> str:
    """Format collected external search sources into a concise prompt representation."""
    if not sources:
        return "No external search evidence retrieved."

    lines: List[str] = []
    for idx, item in enumerate(sources, start=1):
        title = item.get("title", "Untitled")
        url = item.get("url", "")
        source = item.get("source") or "Web"
        stype = item.get("type", "web")
        snippet = item.get("snippet", "")
        # Bounded snippet length to prevent prompt bloating
        if snippet and len(snippet) > 250:
            snippet = snippet[:247] + "..."
        lines.append(
            f"[{idx}] {title}\n"
            f"    Type: {stype} | Source: {source}\n"
            f"    URL: {url}\n"
            f"    Summary: {snippet if snippet else 'N/A'}"
        )
    return "\n".join(lines)


async def _safe_call_tool(tool_name: str, coro) -> List[Dict[str, Any]]:
    """Safely invoke an MCP tool coroutine, isolating individual tool failures."""
    try:
        response: SearchResponse = await coro
        items: List[Dict[str, Any]] = []
        for res in response.results:
            items.append({
                "title": res.title,
                "url": res.url,
                "snippet": (res.snippet or "").strip(),
                "source": res.source or response.provider,
                "type": res.result_type.value if hasattr(res.result_type, "value") else str(res.result_type),
                "published_at": res.published_at or "",
                "provider": response.provider,
            })
        logger.info(f"[RESEARCH_AGENT] Tool '{tool_name}' returned {len(items)} results.")
        return items
    except Exception as e:
        logger.warning(
            f"[RESEARCH_AGENT] MCP Tool '{tool_name}' call failed ({type(e).__name__}): {e}. "
            "Continuing with other search sources."
        )
        return []


async def _fetch_external_search_evidence(
    topic: str,
    audience: str,
    client: Optional[SearchMCPClient] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve external search results concurrently across all four Search MCP tools:
    search_web, search_news, search_trends, and search_research_papers.
    """
    clean_topic = topic.strip() if topic else ""
    if not clean_topic:
        logger.warning("[RESEARCH_AGENT] Empty topic provided; skipping external search.")
        return []

    settings = get_settings()
    # Define concise result limit per tool (default 3 to prevent prompt saturation)
    search_limit = min(getattr(settings, "SEARCH_DEFAULT_LIMIT", 3), 3)

    # Tailor queries: base primarily on topic, adding audience context where valuable
    clean_audience = audience.strip() if audience else ""
    is_specific_audience = bool(
        clean_audience and clean_audience.lower() not in ["general audience", "general", "all", "none", "n/a"]
    )

    web_query = f"{clean_topic} for {clean_audience}" if is_specific_audience else clean_topic
    news_query = clean_topic
    trends_query = clean_topic
    papers_query = clean_topic

    mcp_client = client or get_mcp_client()

    logger.info(
        f"[RESEARCH_AGENT] Querying Search MCP tools for topic='{clean_topic}' (limit={search_limit})"
    )

    tasks = [
        _safe_call_tool("search_web", mcp_client.search_web(web_query, limit=search_limit)),
        _safe_call_tool("search_news", mcp_client.search_news(news_query, limit=search_limit)),
        _safe_call_tool("search_trends", mcp_client.search_trends(trends_query, limit=search_limit)),
        _safe_call_tool("search_research_papers", mcp_client.search_research_papers(papers_query, limit=search_limit)),
    ]

    tool_results = await asyncio.gather(*tasks, return_exceptions=True)

    collected_sources: List[Dict[str, Any]] = []
    seen_urls = set()

    for batch in tool_results:
        if isinstance(batch, list):
            for item in batch:
                url = item.get("url")
                if url and url in seen_urls:
                    continue
                if url:
                    seen_urls.add(url)
                collected_sources.append(item)
        elif isinstance(batch, Exception):
            logger.warning(f"[RESEARCH_AGENT] Search task error: {batch}")

    return collected_sources


async def research_agent_node(
    state: ContentState,
    client: Optional[SearchMCPClient] = None
) -> Dict[str, Any]:
    """
    Research Agent node for Phase 1C-2 content workflow.
    1. Collects live external search evidence via Search MCP tools (web, news, trends, papers).
    2. Isolates individual tool or connection errors gracefully.
    3. Synthesizes structured research insights using the configured LLM grounded in evidence.
    4. Returns updated research and research_sources state.
    """
    topic = state.get("topic", "")
    audience = state.get("audience", "general audience")
    tone = state.get("tone", "educational")
    source_url = state.get("source_url") or "N/A"

    logger.info(f"[RESEARCH_AGENT] Running research for topic='{topic}', audience='{audience}'")

    # Step 1: Retrieve external search evidence via Search MCP
    try:
        collected_sources = await _fetch_external_search_evidence(
            topic=topic,
            audience=audience,
            client=client
        )
    except Exception as e:
        logger.warning(
            f"[RESEARCH_AGENT] External search gathering encountered an error ({type(e).__name__}): {e}. "
            "Proceeding without external evidence."
        )
        collected_sources = []

    if collected_sources:
        logger.info(f"[RESEARCH_AGENT] Collected {len(collected_sources)} external search sources.")
        evidence_text = _format_search_evidence(collected_sources)
    else:
        logger.info("[RESEARCH_AGENT] No external search evidence retrieved. Proceeding with baseline LLM synthesis.")
        evidence_text = "No external search evidence available. Synthesize based on domain knowledge."

    # Step 2: Formulate prompts for LLM synthesis
    system_prompt = (
        "You are a Research Agent specializing in technical content intelligence and personal branding.\n"
        "Your task is to analyze the given topic, target audience, tone, and external search evidence, "
        "and output structured research insights in JSON format.\n\n"
        "Synthesis Guidelines:\n"
        "1. Evidence Grounding: Synthesize insights using the provided external search evidence. "
        "Distinguish verified external evidence from inference.\n"
        "2. Factual Integrity: Do not invent facts, statistics, citations, or URLs. "
        "Only reference sources and URLs that appear in the supplied search evidence.\n"
        "3. Fallback: If external search evidence is unavailable or sparse, synthesize insights using established domain knowledge.\n\n"
        "Required JSON keys:\n"
        "- 'key_concepts': list of main concepts/themes\n"
        "- 'audience_insights': analysis of what appeals to the target audience\n"
        "- 'key_hooks': list of engaging angles/hooks\n"
        "- 'relevant_context': summary of topic context and synthesized evidence\n"
        "Do not output markdown codeblocks outside valid JSON."
    )

    user_prompt = (
        f"Research Agent Request:\n"
        f"- Topic: {topic}\n"
        f"- Target Audience: {audience}\n"
        f"- Tone: {tone}\n"
        f"- Source URL: {source_url}\n\n"
        f"External Search Evidence:\n"
        f"{evidence_text}\n"
    )

    # Step 3: Invoke LLM and parse structured output
    try:
        llm = get_llm()
        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])

        content = response.content.strip()
        # Clean JSON codeblock wrappers if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        parsed_data = json.loads(content.strip())
        if not isinstance(parsed_data, dict):
            raise ValueError("Parsed LLM output is not a dictionary.")

        # Ensure all required keys exist
        for key in ["key_concepts", "audience_insights", "key_hooks", "relevant_context"]:
            if key not in parsed_data:
                raise ValueError(f"Missing required key '{key}' in research output.")

        research_data = parsed_data
    except Exception as e:
        logger.warning(f"[RESEARCH_AGENT] LLM JSON parsing or execution fallback: {e}")
        research_data = {
            "key_concepts": [topic, "Workflow Automation", "AI Engineering"],
            "audience_insights": f"Tailored insights for {audience}.",
            "key_hooks": [f"Unlocking the power of {topic}", "Why developers are adopting agentic workflows"],
            "relevant_context": f"Synthesized research regarding {topic} with {tone} tone."
        }

    return {
        "research": research_data,
        "research_sources": collected_sources,
    }
