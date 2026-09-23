import json
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage

from app.workflows.state import ContentState
from app.core.llm import get_llm
from app.core.logging import logger


async def content_generator_node(state: ContentState) -> Dict[str, Any]:
    """
    Content Generator node for Phase 1A workflow.
    Consumes topic, platforms, audience, tone, research, and strategy,
    and generates platform-tailored post content (primarily LinkedIn).
    """
    logger.info(f"[CONTENT_GENERATOR] Generating content for topic='{state.get('topic')}' on platforms={state.get('platforms')}")

    topic = state.get("topic", "")
    platforms = state.get("platforms", ["linkedin"])
    audience = state.get("audience", "software engineers")
    tone = state.get("tone", "educational")
    research = state.get("research", {})
    strategy = state.get("strategy", {})

    system_prompt = (
        "You are an AI Content Generator Agent specialized in personal branding posts.\n"
        "Your goal is to generate high-performing, high-engagement content for target platforms (primarily LinkedIn).\n"
        "Produce JSON mapping each requested platform key to its generated content object.\n"
        "Required format per platform key (e.g. 'linkedin'):\n"
        "{\n"
        "  'title': 'Engaging title',\n"
        "  'content': 'Full body text of the post with emojis, spacing, line breaks',\n"
        "  'hashtags': ['#Tag1', '#Tag2'],\n"
        "  'call_to_action': 'Clear closing question/CTA'\n"
        "}\n"
        "Do not output markdown codeblocks outside valid JSON."
    )

    user_prompt = (
        f"Content Generator Request:\n"
        f"- Topic: {topic}\n"
        f"- Target Platforms: {', '.join(platforms)}\n"
        f"- Audience: {audience}\n"
        f"- Tone: {tone}\n"
        f"- Research: {json.dumps(research)}\n"
        f"- Strategy: {json.dumps(strategy)}\n"
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

        generated_content = json.loads(content.strip())
    except Exception as e:
        logger.warning(f"[CONTENT_GENERATOR] LLM JSON parsing or execution fallback: {e}")
        
        # Default structured fallback content for requested platforms
        generated_content = {}
        for p in platforms:
            p_key = p.lower()
            if p_key == "linkedin":
                generated_content[p_key] = {
                    "title": f"Mastering {topic}: An Executive Guide",
                    "content": (
                        f"🚀 {topic} is changing how we approach modern tech stacks!\n\n"
                        f"As {audience}, staying ahead means leveraging automated agentic workflows. "
                        f"Here is a key framework for success:\n\n"
                        f"1️⃣ State-Driven Execution (LangGraph)\n"
                        f"2️⃣ Specialized Agent Roles\n"
                        f"3️⃣ Scalable Infrastructure\n\n"
                        f"What are your main takeaways? Drop a line below!"
                    ),
                    "hashtags": [f"#{topic.replace(' ', '')}", "#AIEngineering", "#Technology", "#Innovation"],
                    "call_to_action": f"Share your experience with {topic} in the comments below! 👇"
                }
            else:
                generated_content[p_key] = {
                    "title": f"Quick Update: {topic}",
                    "content": f"Exploring {topic} for {audience}. Key focus: {tone} insight.",
                    "hashtags": [f"#{topic.replace(' ', '')}"],
                    "call_to_action": "Let us know your thoughts!"
                }

    return {"generated_content": generated_content}
