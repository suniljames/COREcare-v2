"""Tests for the health endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_healthz_returns_ok(client: AsyncClient) -> None:
    """GIVEN the app is running WHEN GET /healthz THEN returns 200 with status ok."""
    response = await client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_nonexistent_route_returns_404(client: AsyncClient) -> None:
    """GIVEN the app is running WHEN GET /nonexistent THEN returns 404."""
    response = await client.get("/nonexistent")
    assert response.status_code == 404
