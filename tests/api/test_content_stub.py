import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_content_generation_workflow(async_client: AsyncClient):
    """Test POST /api/v1/content/generate Phase 1A workflow execution."""
    request_payload = {
        "topic": "AI agents in software development",
        "platforms": ["linkedin"],
        "audience": "software engineers",
        "tone": "educational"
    }

    response = await async_client.post("/api/v1/content/generate", json=request_payload)
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "success"
    assert "data" in payload

    data = payload["data"]
    assert "run_id" in data
    assert data["run_id"].startswith("run_")
    assert data["status"] == "completed"
    assert data["requested_topic"] == "AI agents in software development"
    assert data["platforms"] == ["linkedin"]
    assert "generated_content" in data and data["generated_content"] is not None
    assert "linkedin" in data["generated_content"]
    assert "research" in data and data["research"] is not None
    assert "strategy" in data and data["strategy"] is not None


@pytest.mark.asyncio
async def test_content_generation_validation_error(async_client: AsyncClient):
    """Test payload validation for missing required topic field."""
    invalid_payload = {
        "platforms": ["linkedin"]
    }

    response = await async_client.post("/api/v1/content/generate", json=invalid_payload)
    assert response.status_code == 422
