import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient):
    """Test API root welcome endpoint."""
    response = await async_client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert "version" in payload["data"]


@pytest.mark.asyncio
async def test_health_endpoint_schema(async_client: AsyncClient):
    """Test /api/v1/health endpoint response schema structure."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code in [200, 503]
    payload = response.json()
    assert "status" in payload
    assert "message" in payload
    assert "data" in payload
    assert "timestamp" in payload
    
    data = payload["data"]
    assert "database" in data
    assert "connected" in data["database"]
    assert "database_name" in data["database"]
