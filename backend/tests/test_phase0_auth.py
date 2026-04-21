"""
Phase 0 Tests — Authentication & RBAC
Tests JWT login, token validation, and role-based access control.
"""
import pytest
from httpx import AsyncClient


# ─────────────────────────────────────────────
# AUTH — LOGIN
# ─────────────────────────────────────────────

class TestLogin:
    async def test_admin_login_returns_token(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/login", data={
            "username": "admin",
            "password": "admin123"
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert len(body["access_token"]) > 20  # real JWT, not empty string

    async def test_wrong_password_returns_400(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/login", data={
            "username": "admin",
            "password": "wrongpassword"
        })
        assert resp.status_code == 400

    async def test_nonexistent_user_returns_400(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/login", data={
            "username": "ghost_user",
            "password": "anything"
        })
        assert resp.status_code == 400

    async def test_missing_username_returns_422(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/login", data={
            "password": "postgres"
        })
        assert resp.status_code == 422

    async def test_missing_password_returns_422(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/login", data={
            "username": "admin"
        })
        assert resp.status_code == 422


# ─────────────────────────────────────────────
# AUTH — TOKEN VALIDATION
# ─────────────────────────────────────────────

class TestTokenValidation:
    async def test_no_token_returns_401(self, client: AsyncClient):
        resp = await client.get("/api/v1/sources/")
        assert resp.status_code == 401

    async def test_malformed_token_returns_401(self, client: AsyncClient):
        resp = await client.get("/api/v1/sources/", headers={
            "Authorization": "Bearer this.is.not.a.jwt"
        })
        assert resp.status_code == 401

    async def test_wrong_scheme_returns_401(self, client: AsyncClient):
        resp = await client.get("/api/v1/sources/", headers={
            "Authorization": "Basic admin:postgres"
        })
        assert resp.status_code == 401

    async def test_valid_token_grants_access(self, client: AsyncClient, admin_token: str):
        resp = await client.get("/api/v1/sources/", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert resp.status_code == 200


# ─────────────────────────────────────────────
# RBAC — ANALYST CANNOT DO ADMIN ACTIONS
# ─────────────────────────────────────────────

class TestRBAC:
    async def test_analyst_cannot_create_source(
        self, client: AsyncClient, analyst_token: str
    ):
        resp = await client.post("/api/v1/sources/",
            headers={"Authorization": f"Bearer {analyst_token}"},
            json={
                "name": "Should Be Blocked",
                "category": "community",
                "trust_tier": "LOW",
                "default_weight": 0.3
            }
        )
        assert resp.status_code == 403

    async def test_analyst_cannot_delete_source(
        self, client: AsyncClient, analyst_token: str, created_source: dict
    ):
        source_id = created_source["id"]
        resp = await client.delete(f"/api/v1/sources/{source_id}",
            headers={"Authorization": f"Bearer {analyst_token}"}
        )
        assert resp.status_code == 403

    async def test_analyst_can_read_sources(
        self, client: AsyncClient, analyst_token: str
    ):
        resp = await client.get("/api/v1/sources/",
            headers={"Authorization": f"Bearer {analyst_token}"}
        )
        assert resp.status_code == 200

    async def test_analyst_can_ingest_indicators(
        self, client: AsyncClient, analyst_token: str, created_source: dict
    ):
        resp = await client.post("/api/v1/indicators/",
            headers={"Authorization": f"Bearer {analyst_token}"},
            json={
                "source_id": created_source["id"],
                "indicators": [{"type": "ipv4", "value": "5.5.5.5"}]
            }
        )
        assert resp.status_code in (200, 202)
