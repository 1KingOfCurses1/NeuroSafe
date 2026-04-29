import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_200(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_root_returns_app_name(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "NeuroSafe Backend"


@pytest.mark.asyncio
async def test_demo_config_endpoint(client: AsyncClient):
    response = await client.get("/api/analyze/demo/config")
    assert response.status_code == 200
    data = response.json()
    assert "model_provider" in data
    assert "is_demo_mode" in data
    assert isinstance(data["features"], dict)
