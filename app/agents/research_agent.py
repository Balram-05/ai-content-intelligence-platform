import json
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage

from app.workflows.state import ContentState
from app.core.llm import get_llm
from app.core.logging import logger


async def research_agent_node(state: ContentState) -> Dict[str, Any]:
    """
    Research Agent node for Phase 1A content workflow.
    Receives topic, audience, tone, and source_url from state,
    performs structured research using the configured LLM,
    and returns updated research state.
    """
    logger.info(f"[RESEARCH_AGENT] Running research for topic='{state.get('topic')}'")

    topic = state.get("topic", "")
    audience = state.get("audience", "general audience")
    tone = state.get("tone", "educational")
    source_url = state.get("source_url") or "N/A"

    system_prompt = (
        "You are a Research Agent specializing in technical content intelligence. "
        "Your task is to analyze the given topic and context, and output structured research insights in JSON format.\n"
        "Required JSON keys:\n"
        "- 'key_concepts': list of main concepts/themes\n"
        "- 'audience_insights': analysis of what appeals to the target audience\n"
        "- 'key_hooks': list of engaging angles/hooks\n"
        "- 'relevant_context': summary of topic context\n"
        "Do not output markdown codeblocks outside valid JSON."
    )

    user_prompt = (
        f"Research Agent Request:\n"
        f"- Topic: {topic}\n"
        f"- Target Audience: {audience}\n"
        f"- Tone: {tone}\n"
        f"- Source URL: {source_url}\n"
    )

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
        
        research_data = json.loads(content.strip())
    except Exception as e:
        logger.warning(f"[RESEARCH_AGENT] LLM JSON parsing or execution fallback: {e}")
        research_data = {
            "key_concepts": [topic, "Workflow Automation", "AI Engineering"],
            "audience_insights": f"Tailored insights for {audience}.",
            "key_hooks": [f"Unlocking the power of {topic}", "Why developers are adopting agentic workflows"],
            "relevant_context": f"Synthesized research regarding {topic} with {tone} tone."
        }

    return {"research": research_data}
