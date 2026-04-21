"""
conftest.py — Shared fixtures for all TIP test phases.
Place this file in your tests/ directory (or root tests/ folder).

Usage:
    pytest tests/ -v
    pytest tests/test_phase0_auth.py -v
    pytest tests/ -k "not TestDecay" -v    # skip slow decay tests
"""
import pytest
import pytest_asyncio
import httpx


# ─── Configuration ────────────────────────────────────────────────────────────

BASE_URL = "http://localhost:8000"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

ANALYST_USERNAME = "analyst"
ANALYST_PASSWORD = "analyst123"


# ─── Client ───────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client():
    """Shared async HTTP client for all tests."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as c:
        yield c


# ─── Tokens ───────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def admin_token(client: httpx.AsyncClient) -> str:
    resp = await client.post("/api/v1/auth/login", data={
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD
    })
    assert resp.status_code == 200, (
        f"Admin login failed ({resp.status_code}): {resp.text}\n"
        "Make sure the admin seed ran successfully."
    )
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def analyst_token(client: httpx.AsyncClient) -> str:
    resp = await client.post("/api/v1/auth/login", data={
        "username": ANALYST_USERNAME,
        "password": ANALYST_PASSWORD
    })
    if resp.status_code != 200:
        pytest.skip(f"Analyst user not found ({ANALYST_USERNAME}) — create it first via admin.")
    return resp.json()["access_token"]


# ─── Headers ──────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def admin_headers(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest_asyncio.fixture
async def analyst_headers(analyst_token: str) -> dict:
    return {"Authorization": f"Bearer {analyst_token}"}


# ─── Source fixture ───────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def created_source(client: httpx.AsyncClient, admin_headers: dict) -> dict:
    """
    Creates a reusable test source with a unique name to avoid collisions.
    Deleted automatically after the test via finalizer.
    """
    import uuid
    uid = uuid.uuid4().hex[:6]
    resp = await client.post("/api/v1/sources/", headers=admin_headers, json={
        "name": f"Pytest Source {uid} - Auto Cleanup",
        "category": "community",
        "trust_tier": "HIGH",
        "default_weight": 1.0,
        "intent_description": "Created by pytest fixture, cleaned up after test",
        "is_active": True
    })
    assert resp.status_code in (200, 201), (
        f"Failed to create test source: {resp.status_code} {resp.text}"
    )
    source = resp.json()

    yield source

    # Teardown — best-effort delete (may already be deleted by delete tests)
    await client.delete(
        f"/api/v1/sources/{source['id']}",
        headers=admin_headers
    )


# ─── pytest.ini settings (add to pyproject.toml instead if preferred) ─────────
#
# [tool.pytest.ini_options]
# asyncio_mode = "auto"
# testpaths = ["tests"]
# addopts = "-v --tb=short"
