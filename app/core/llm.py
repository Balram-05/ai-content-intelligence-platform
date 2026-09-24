import json
from typing import Optional, Dict, Any
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, AIMessage

from app.core.config import get_settings
from app.core.logging import logger


class MockLLM(BaseChatModel):
    """
    Keyless Fallback Mock LLM for local development and unit tests.
    Explicitly separated from real LLM execution.
    """

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        # Extract prompt content to produce deterministic structured JSON mock responses
        last_msg = messages[-1].content if messages else ""
        
        if "Research Agent" in last_msg or "research" in last_msg.lower():
            response_content = json.dumps({
                "key_concepts": ["AI Agents", "Automated Workflows", "LangGraph State Machines"],
                "audience_insights": "Software engineers and AI practitioners interested in modular AI agent pipelines.",
                "key_hooks": ["How AI Agents are modernizing developer workflows", "From LLM prompts to graph workflows"],
                "relevant_context": "Phase 1A research synthesis on topic."
            })
        elif "Strategy Agent" in last_msg or "strategy" in last_msg.lower():
            response_content = json.dumps({
                "angle": "Educational deep-dive into practical AI engineering",
                "target_platform_positioning": "LinkedIn professional authority post",
                "structural_outline": ["Hook", "Core Concept", "Architecture Diagram / Flow", "Call to Action"],
                "cta_strategy": "Invite developers to comment with their current AI agent stack."
            })
        else:
            response_content = json.dumps({
                "linkedin": {
                    "title": "Building Agentic AI Workflows with LangGraph",
                    "content": (
                        "🚀 AI Agents are transforming software engineering!\n\n"
                        "Instead of single-prompt chains, modern content engines use stateful graph workflows. "
                        "Here is how Supervisor -> Research -> Strategy -> Generation brings deterministic control to AI outputs.\n\n"
                        "Key Takeaways:\n"
                        "1. Modular State Machines (LangGraph)\n"
                        "2. Specialized Agent Nodes\n"
                        "3. Clean Service & API Boundaries\n\n"
                        "Are you using agentic workflows in production yet? Let's discuss in the comments! 👇"
                    ),
                    "hashtags": ["#AIEngineering", "#LangGraph", "#Python", "#SoftwareEngineering"],
                    "call_to_action": "Comment below with your thoughts!"
                }
            })

        return type("ChatResult", (), {
            "generations": [
                type("ChatGeneration", (), {
                    "message": AIMessage(content=response_content),
                    "text": response_content
                })()
            ]
        })()

    @property
    def _llm_type(self) -> str:
        return "keyless_mock_llm"

def is_valid_api_key(api_key: Optional[str]) -> bool:
    """Checks whether an API key is present and not a dummy placeholder."""
    if not api_key or not api_key.strip():
        return False

    key = api_key.strip().lower()

    if (
        "your_openai_api_key" in key
        or "your_groq_api_key" in key
        or key.startswith("sk-dummy")
        or key.startswith("gsk-dummy")
        or key == "none"
    ):
        return False

    return True

def get_llm():
    """
    Factory function supplying the configured LLM instance.

    Supports OpenAI and Groq providers.
    Falls back to MockLLM when the configured provider
    does not have a valid API key.
    """
    settings = get_settings()

    provider = settings.LLM_PROVIDER.lower().strip()

    if provider == "groq":
        if is_valid_api_key(settings.GROQ_API_KEY):
            logger.info(
                f"[LLM_EXECUTION_MODE] Using REAL ChatGroq "
                f"(model='{settings.GROQ_MODEL}')"
            )

            return ChatGroq(
                api_key=settings.GROQ_API_KEY,
                model=settings.GROQ_MODEL,
                temperature=0.7,
            )

        logger.warning(
            "[LLM_EXECUTION_MODE] GROQ_API_KEY not configured "
            "or dummy key detected. Using MOCK Fallback LLM."
        )
        return MockLLM()

    if provider == "openai":
        if is_valid_api_key(settings.OPENAI_API_KEY):
            logger.info(
                f"[LLM_EXECUTION_MODE] Using REAL ChatOpenAI "
                f"(model='{settings.OPENAI_MODEL}')"
            )

            return ChatOpenAI(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL,
                temperature=0.7,
            )

        logger.warning(
            "[LLM_EXECUTION_MODE] OPENAI_API_KEY not configured "
            "or dummy key detected. Using MOCK Fallback LLM."
        )
        return MockLLM()

    logger.warning(
        f"[LLM_EXECUTION_MODE] Unknown LLM provider '{provider}'. "
        "Using MOCK Fallback LLM."
    )
    return MockLLM()