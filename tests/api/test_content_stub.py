import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_content_generation_stub(async_client: AsyncClient):
    """Test POST /api/v1/content/generate temporary stub endpoint."""
    request_payload = {
        "topic": "Model Context Protocol",
        "platforms": ["linkedin", "twitter"],
        "audience": "AI engineers",
        "tone": "technical"
    }
    
    response = await async_client.post("/api/v1/content/generate", json=request_payload)
    assert response.status_code == 202
    
    payload = response.json()
    assert payload["status"] == "success"
    assert "data" in payload
    
    data = payload["data"]
    assert "run_id" in data
    assert data["run_id"].startswith("run_")
    assert data["status"] == "queued"
    assert data["requested_topic"] == "Model Context Protocol"
    assert data["platforms"] == ["linkedin", "twitter"]


@pytest.mark.asyncio
async def test_content_generation_stub_validation_error(async_client: AsyncClient):
    """Test payload validation for missing required topic field."""
    invalid_payload = {
        "platforms": ["linkedin"]
    }
    
    response = await async_client.post("/api/v1/content/generate", json=invalid_payload)
    assert response.status_code == 422
