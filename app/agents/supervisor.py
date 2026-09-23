from typing import Dict, Any
from app.workflows.state import ContentState
from app.core.logging import logger


async def supervisor_node(state: ContentState) -> Dict[str, Any]:
    """
    Phase 1A Supervisor Node.
    Determines next stage in the deterministic pipeline:
    Supervisor -> Research -> Strategy -> Content Generator -> END.
    """
    if not state.get("research"):
        next_step = "research"
    elif not state.get("strategy"):
        next_step = "strategy"
    elif not state.get("generated_content"):
        next_step = "content_generator"
    else:
        next_step = "finish"

    logger.info(f"[SUPERVISOR] State evaluation complete. Next step -> '{next_step}'")
    return {"next_step": next_step}


def supervisor_router(state: ContentState) -> str:
    """
    Conditional edge router for LangGraph.
    Returns destination node name based on state's next_step field.
    """
    return state.get("next_step", "finish")
