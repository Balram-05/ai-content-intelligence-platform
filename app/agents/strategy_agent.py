import json
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage

from app.workflows.state import ContentState
from app.core.llm import get_llm
from app.core.logging import logger


async def strategy_agent_node(state: ContentState) -> Dict[str, Any]:
    """
    Strategy Agent node for Phase 1A content workflow.
    Consumes topic, platforms, audience, tone, and research from state,
    formulates a platform-specific content strategy,
    and returns updated strategy state.
    """
    logger.info(f"[STRATEGY_AGENT] Running strategy for topic='{state.get('topic')}'")

    topic = state.get("topic", "")
    platforms = state.get("platforms", ["linkedin"])
    audience = state.get("audience", "general audience")
    tone = state.get("tone", "educational")
    research = state.get("research", {})

    system_prompt = (
        "You are a Content Strategy Agent specializing in personal branding and content planning. "
        "Your task is to take topic information, target platforms, audience profile, tone, and research synthesis, "
        "and produce a structured content strategy in JSON format.\n"
        "Required JSON keys:\n"
        "- 'angle': core narrative angle/hook strategy\n"
        "- 'target_platform_positioning': strategy per platform\n"
        "- 'structural_outline': list of section topics for content generation\n"
        "- 'cta_strategy': approach for call-to-action engagement\n"
        "Do not output markdown codeblocks outside valid JSON."
    )

    user_prompt = (
        f"Strategy Agent Request:\n"
        f"- Topic: {topic}\n"
        f"- Platforms: {', '.join(platforms)}\n"
        f"- Audience: {audience}\n"
        f"- Desired Tone: {tone}\n"
        f"- Research Context: {json.dumps(research)}\n"
    )

    try:
        llm = get_llm()
        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])

        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        strategy_data = json.loads(content.strip())
    except Exception as e:
        logger.warning(f"[STRATEGY_AGENT] LLM JSON parsing or execution fallback: {e}")
        strategy_data = {
            "angle": f"Deep-dive technical breakdown of {topic}",
            "target_platform_positioning": f"Professional authority post tailored for {', '.join(platforms)}",
            "structural_outline": ["Attention Hook", "Core Value Proposition", "Key Insights", "Call to Action"],
            "cta_strategy": f"Engage {audience} with a compelling discussion prompt."
        }

    return {"strategy": strategy_data}
