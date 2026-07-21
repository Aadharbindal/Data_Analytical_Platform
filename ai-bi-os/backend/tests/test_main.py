import asyncio
import httpx
from httpx import ASGITransport
from app.main import app


def _get(path: str) -> httpx.Response:
    """
    Drives the ASGI app directly via httpx's ASGITransport instead of
    starlette.testclient.TestClient, whose installed version (pinned by
    fastapi<0.28 compatibility) passes an `app=` kwarg to httpx.Client that
    httpx>=0.28 (required by litellm) removed. httpx.AsyncClient +
    ASGITransport works with the httpx version this project actually needs.
    """
    async def _call():
        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            return await client.get(path)
    return asyncio.run(_call())


def test_health_check():
    response = _get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}
