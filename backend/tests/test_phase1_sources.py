"""
Phase 1 Tests — Source Management (CRUD)
Covers POST, GET (list + detail), PATCH, DELETE /api/v1/sources/
"""
import pytest
import uuid
from httpx import AsyncClient


# ─────────────────────────────────────────────
# POST /api/v1/sources/
# ─────────────────────────────────────────────

class TestCreateSource:
    async def test_create_source_minimal_fields(
        self, client: AsyncClient, admin_headers: dict
    ):
        name = f"Minimal Source {uuid.uuid4().hex[:6]}"
        resp = await client.post("/api/v1/sources/", headers=admin_headers, json={
            "name": name,
            "category": "community",
            "trust_tier": "LOW",
            "default_weight": 0.3
        })
        assert resp.status_code in (200, 201)
        body = resp.json()
        assert body["name"] == name
        assert body["trust_tier"] == "LOW"
        assert "id" in body
        assert "created_at" in body

    async def test_create_source_all_fields(
        self, client: AsyncClient, admin_headers: dict
    ):
        name = f"Full Source {uuid.uuid4().hex[:6]}"
        resp = await client.post("/api/v1/sources/", headers=admin_headers, json={
            "name": name,
            "category": "commercial",
            "trust_tier": "HIGH",
            "default_weight": 1.0,
            "intent_description": "Premium commercial feed",
            "pull_url": "https://feeds.example.com/iocs.json",
            "pull_schedule": "0 */6 * * *",
            "is_active": True
        })
        assert resp.status_code in (200, 201)
        body = resp.json()
        assert body["category"] == "commercial"
        assert body["trust_tier"] == "HIGH"
        assert body["pull_url"] == "https://feeds.example.com/iocs.json"
        assert body["is_active"] is True

    async def test_create_source_inactive_by_default_when_specified(
        self, client: AsyncClient, admin_headers: dict
    ):
        name = f"Inactive Placeholder {uuid.uuid4().hex[:6]}"
        resp = await client.post("/api/v1/sources/", headers=admin_headers, json={
            "name": name,
            "category": "community",
            "trust_tier": "LOW",
            "default_weight": 0.3,
            "pull_url": "http://example.com/placeholder.txt",
            "is_active": False
        })
        assert resp.status_code in (200, 201)
        assert resp.json()["is_active"] is False

    async def test_create_source_duplicate_name_returns_409(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        resp = await client.post("/api/v1/sources/", headers=admin_headers, json={
            "name": created_source["name"],   # same name as fixture
            "category": "community",
            "trust_tier": "LOW",
            "default_weight": 0.3
        })
        assert resp.status_code == 409

    async def test_create_source_invalid_trust_tier_returns_422(
        self, client: AsyncClient, admin_headers: dict
    ):
        resp = await client.post("/api/v1/sources/", headers=admin_headers, json={
            "name": "Bad Tier Source",
            "category": "community",
            "trust_tier": "ULTRA",        # invalid enum value
            "default_weight": 0.3
        })
        assert resp.status_code == 422

    async def test_create_source_invalid_category_returns_422(
        self, client: AsyncClient, admin_headers: dict
    ):
        resp = await client.post("/api/v1/sources/", headers=admin_headers, json={
            "name": "Bad Cat Source",
            "category": "unknown_category",  # invalid
            "trust_tier": "LOW",
            "default_weight": 0.3
        })
        assert resp.status_code == 422

    async def test_create_source_weight_out_of_range_returns_422(
        self, client: AsyncClient, admin_headers: dict
    ):
        resp = await client.post("/api/v1/sources/", headers=admin_headers, json={
            "name": "Weight Bad",
            "category": "community",
            "trust_tier": "LOW",
            "default_weight": 999.99     # should be 0.0 - 1.0
        })
        assert resp.status_code == 422

    async def test_create_source_missing_required_fields_returns_422(
        self, client: AsyncClient, admin_headers: dict
    ):
        resp = await client.post("/api/v1/sources/", headers=admin_headers, json={
            "name": "Missing Fields Source"
            # missing: category, trust_tier, default_weight
        })
        assert resp.status_code == 422

    async def test_create_source_response_schema(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Every field in the response contract must be present."""
        name = f"Schema Check Source {uuid.uuid4().hex[:6]}"
        resp = await client.post("/api/v1/sources/", headers=admin_headers, json={
            "name": name,
            "category": "research",
            "trust_tier": "MEDIUM",
            "default_weight": 0.6
        })
        body = resp.json()
        required_fields = {
            "id", "name", "category", "trust_tier",
            "default_weight", "is_active", "created_at"
        }
        assert required_fields.issubset(body.keys())


# ─────────────────────────────────────────────
# GET /api/v1/sources/
# ─────────────────────────────────────────────

class TestListSources:
    async def test_list_sources_returns_array(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        resp = await client.get("/api/v1/sources/", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) >= 1

    async def test_list_sources_contains_created_source(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        resp = await client.get("/api/v1/sources/", headers=admin_headers)
        ids = [s["id"] for s in resp.json()]
        assert created_source["id"] in ids

    async def test_list_sources_each_item_has_required_fields(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        resp = await client.get("/api/v1/sources/", headers=admin_headers)
        for source in resp.json():
            assert "id" in source
            assert "name" in source
            assert "trust_tier" in source
            assert "is_active" in source


# ─────────────────────────────────────────────
# GET /api/v1/sources/{source_id}
# ─────────────────────────────────────────────

class TestGetSource:
    async def test_get_source_by_id(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        source_id = created_source["id"]
        resp = await client.get(f"/api/v1/sources/{source_id}", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == source_id
        assert body["name"] == created_source["name"]

    async def test_get_source_nonexistent_returns_404(
        self, client: AsyncClient, admin_headers: dict
    ):
        resp = await client.get(
            "/api/v1/sources/00000000-0000-0000-0000-000000000000",
            headers=admin_headers
        )
        assert resp.status_code == 404

    async def test_get_source_invalid_uuid_returns_400_or_422(
        self, client: AsyncClient, admin_headers: dict
    ):
        resp = await client.get("/api/v1/sources/not-a-uuid", headers=admin_headers)
        assert resp.status_code in (400, 422)


# ─────────────────────────────────────────────
# PATCH /api/v1/sources/{source_id}
# ─────────────────────────────────────────────

class TestUpdateSource:
    async def test_patch_source_name(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        source_id = created_source["id"]
        resp = await client.patch(f"/api/v1/sources/{source_id}",
            headers=admin_headers,
            json={"name": "Updated Source Name"}
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Source Name"

    async def test_patch_source_deactivate(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        source_id = created_source["id"]
        resp = await client.patch(f"/api/v1/sources/{source_id}",
            headers=admin_headers,
            json={"is_active": False}
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    async def test_patch_source_trust_tier(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        source_id = created_source["id"]
        resp = await client.patch(f"/api/v1/sources/{source_id}",
            headers=admin_headers,
            json={"trust_tier": "HIGH"}
        )
        assert resp.status_code == 200
        assert resp.json()["trust_tier"] == "HIGH"

    async def test_patch_source_id_unchanged(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        """PATCH must not change the source's ID."""
        source_id = created_source["id"]
        resp = await client.patch(f"/api/v1/sources/{source_id}",
            headers=admin_headers,
            json={"name": "ID Should Not Change"}
        )
        assert resp.json()["id"] == source_id

    async def test_patch_nonexistent_source_returns_404(
        self, client: AsyncClient, admin_headers: dict
    ):
        resp = await client.patch(
            "/api/v1/sources/00000000-0000-0000-0000-000000000000",
            headers=admin_headers,
            json={"name": "Ghost"}
        )
        assert resp.status_code == 404

    async def test_patch_source_invalid_trust_tier_returns_422(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        resp = await client.patch(f"/api/v1/sources/{created_source['id']}",
            headers=admin_headers,
            json={"trust_tier": "SUPER_HIGH"}
        )
        assert resp.status_code == 422


# ─────────────────────────────────────────────
# DELETE /api/v1/sources/{source_id}
# ─────────────────────────────────────────────

class TestDeleteSource:
    async def test_delete_source(
        self, client: AsyncClient, admin_headers: dict
    ):
        # Create a dedicated source to delete so other tests aren't affected
        name = f"To Be Deleted {uuid.uuid4().hex[:6]}"
        create_resp = await client.post("/api/v1/sources/", headers=admin_headers, json={
            "name": name,
            "category": "community",
            "trust_tier": "LOW",
            "default_weight": 0.3
        })
        source_id = create_resp.json()["id"]

        del_resp = await client.delete(f"/api/v1/sources/{source_id}", headers=admin_headers)
        assert del_resp.status_code in (200, 204)

        # Confirm it's gone
        get_resp = await client.get(f"/api/v1/sources/{source_id}", headers=admin_headers)
        assert get_resp.status_code == 404

    async def test_delete_nonexistent_source_returns_404(
        self, client: AsyncClient, admin_headers: dict
    ):
        resp = await client.delete(
            "/api/v1/sources/00000000-0000-0000-0000-000000000000",
            headers=admin_headers
        )
        assert resp.status_code == 404
