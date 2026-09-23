from langgraph.graph import StateGraph, START, END

from app.workflows.state import ContentState
from app.agents.supervisor import supervisor_node, supervisor_router
from app.agents.research_agent import research_agent_node
from app.agents.strategy_agent import strategy_agent_node
from app.agents.content_generator import content_generator_node
from app.core.logging import logger


def build_content_workflow():
    """
    Constructs and compiles the Phase 1A LangGraph workflow graph:
    START -> Supervisor -> Research -> Strategy -> Content Generator -> END.
    """
    builder = StateGraph(ContentState)

    # Register workflow nodes
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("research", research_agent_node)
    builder.add_node("strategy", strategy_agent_node)
    builder.add_node("content_generator", content_generator_node)

    # Entry point connects to supervisor
    builder.add_edge(START, "supervisor")

    # Supervisor conditional routing
    builder.add_conditional_edges(
        "supervisor",
        supervisor_router,
        {
            "research": "research",
            "strategy": "strategy",
            "content_generator": "content_generator",
            "finish": END
        }
    )

    # Each agent returns to supervisor for state verification and routing
    builder.add_edge("research", "supervisor")
    builder.add_edge("strategy", "supervisor")
    builder.add_edge("content_generator", "supervisor")

    return builder.compile()


# Global compiled workflow graph instance
content_workflow_graph = build_content_workflow()


async def run_content_generation_workflow(initial_state: ContentState) -> ContentState:
    """
    Public async interface for ContentService to invoke the LangGraph pipeline.
    """
    logger.info("[CONTENT_WORKFLOW] Executing LangGraph pipeline...")
    final_state = await content_workflow_graph.ainvoke(initial_state)
    logger.info("[CONTENT_WORKFLOW] Pipeline execution complete.")
    return final_state
