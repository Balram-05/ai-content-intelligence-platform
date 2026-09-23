import pytest
from app.workflows.state import ContentState
from app.agents.supervisor import supervisor_node, supervisor_router
from app.agents.research_agent import research_agent_node
from app.agents.strategy_agent import strategy_agent_node
from app.agents.content_generator import content_generator_node
from app.workflows.content_graph import run_content_generation_workflow


@pytest.mark.asyncio
async def test_supervisor_routing():
    """Test supervisor deterministic routing logic."""
    state_empty: ContentState = {"topic": "Test topic"}
    node_out = await supervisor_node(state_empty)
    assert node_out["next_step"] == "research"
    assert supervisor_router({"next_step": "research"}) == "research"

    state_researched: ContentState = {"topic": "Test topic", "research": {"key": "val"}}
    node_out = await supervisor_node(state_researched)
    assert node_out["next_step"] == "strategy"

    state_strategized: ContentState = {"topic": "Test topic", "research": {"key": "val"}, "strategy": {"strat": "val"}}
    node_out = await supervisor_node(state_strategized)
    assert node_out["next_step"] == "content_generator"

    state_done: ContentState = {
        "topic": "Test topic",
        "research": {"key": "val"},
        "strategy": {"strat": "val"},
        "generated_content": {"linkedin": {}}
    }
    node_out = await supervisor_node(state_done)
    assert node_out["next_step"] == "finish"


@pytest.mark.asyncio
async def test_full_content_workflow():
    """Test end-to-end execution of LangGraph content workflow graph."""
    initial_state: ContentState = {
        "topic": "AI agents in software development",
        "platforms": ["linkedin"],
        "audience": "software engineers",
        "tone": "educational"
    }

    final_state = await run_content_generation_workflow(initial_state)

    assert final_state.get("research") is not None
    assert final_state.get("strategy") is not None
    assert final_state.get("generated_content") is not None
    assert "linkedin" in final_state["generated_content"]
