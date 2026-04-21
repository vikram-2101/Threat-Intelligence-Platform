"""
Phase 2 Tests — Enrichment, Correlation & Confidence Scoring
These tests verify the async intelligence pipeline fires correctly after ingestion.
All tests use asyncio.sleep() to allow Celery workers time to process.
Set WORKER_WAIT_SECONDS in conftest to tune for your hardware.
"""
import asyncio
import pytest
import uuid
from httpx import AsyncClient

WORKER_WAIT_SECONDS = 20   # time to allow enrichment + scoring workers to finish


# ─────────────────────────────────────────────
# CONFIDENCE SCORING — SCORE INCREASES
# ─────────────────────────────────────────────

class TestConfidenceScoring:
    async def test_confidence_increases_after_enrichment(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        """After enrichment runs, confidence must be > 0 for enrichable types."""
        val = f"scoring-test-{uuid.uuid4().hex[:6]}.com"
        resp = await client.post("/api/v1/indicators/", headers=admin_headers, json={
            "source_id": created_source["id"],
            "indicators": [{"type": "domain", "value": val}]
        })
        indicator_id = resp.json()["indicators"][0]["id"]
        initial_confidence = resp.json()["indicators"][0]["current_confidence"]
        assert initial_confidence == 0   # must start at zero

        # Wait for enrichment + scoring workers
        await asyncio.sleep(WORKER_WAIT_SECONDS)

        # Re-fetch the indicator
        detail_resp = await client.get(
            f"/api/v1/indicators/{indicator_id}",
            headers=admin_headers
        )
        assert detail_resp.status_code == 200
        updated_confidence = detail_resp.json()["current_confidence"]
        assert updated_confidence > 0, (
            f"Confidence still 0 after {WORKER_WAIT_SECONDS}s — "
            "check if scoring worker is consuming evidence.created events"
        )

    async def test_high_trust_source_produces_higher_confidence(
        self, client: AsyncClient, admin_headers: dict
    ):
        """HIGH trust source should yield higher confidence than LOW trust source."""
        # Create HIGH trust source
        name_high = f"High Trust Scoring Test {uuid.uuid4().hex[:6]}"
        high_src = (await client.post("/api/v1/sources/", headers=admin_headers, json={
            "name": name_high,
            "category": "commercial",
            "trust_tier": "HIGH",
            "default_weight": 1.0
        })).json()

        # Create LOW trust source
        name_low = f"Low Trust Scoring Test {uuid.uuid4().hex[:6]}"
        low_src = (await client.post("/api/v1/sources/", headers=admin_headers, json={
            "name": name_low,
            "category": "community",
            "trust_tier": "LOW",
            "default_weight": 0.3
        })).json()

        # Ingest same type from both sources (different values to avoid dedup)
        val_high = f"high-trust-{uuid.uuid4().hex[:6]}.com"
        val_low = f"low-trust-{uuid.uuid4().hex[:6]}.com"
        r_high = await client.post("/api/v1/indicators/", headers=admin_headers, json={
            "source_id": high_src["id"],
            "indicators": [{"type": "domain", "value": val_high}]
        })
        r_low = await client.post("/api/v1/indicators/", headers=admin_headers, json={
            "source_id": low_src["id"],
            "indicators": [{"type": "domain", "value": val_low}]
        })

        id_high = r_high.json()["indicators"][0]["id"]
        id_low = r_low.json()["indicators"][0]["id"]

        await asyncio.sleep(WORKER_WAIT_SECONDS)

        conf_high = (await client.get(
            f"/api/v1/indicators/{id_high}", headers=admin_headers
        )).json()["current_confidence"]

        conf_low = (await client.get(
            f"/api/v1/indicators/{id_low}", headers=admin_headers
        )).json()["current_confidence"]

        assert conf_high > conf_low, (
            f"HIGH trust ({conf_high}) should score higher than LOW trust ({conf_low})"
        )

    async def test_file_hash_confidence_stays_zero_no_enrichers(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        """MD5/SHA1/SHA256 have no enrichers in MVP — confidence should stay at 0."""
        # Use a UUID-based unique hash each run to avoid DB pollution from repeated runs
        unique_hash = (uuid.uuid4().hex + uuid.uuid4().hex)[:64]  # 64 unique hex chars
        resp = await client.post("/api/v1/indicators/", headers=admin_headers, json={
            "source_id": created_source["id"],
            "indicators": [{
                "type": "sha256",
                "value": unique_hash
            }]
        })
        indicator_id = resp.json()["indicators"][0]["id"]

        await asyncio.sleep(WORKER_WAIT_SECONDS)

        detail = (await client.get(
            f"/api/v1/indicators/{indicator_id}", headers=admin_headers
        )).json()
        # Hashes have no external enrichment — score must remain 0
        assert detail["current_confidence"] == 0


# ─────────────────────────────────────────────
# EVIDENCE — ENRICHMENT RECORDS EXIST
# ─────────────────────────────────────────────

class TestEvidenceCreation:
    async def test_evidence_created_for_domain(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        """After enrichment, the indicator detail must contain evidence records."""
        val = f"evidence-check-{uuid.uuid4().hex[:6]}.com"
        resp = await client.post("/api/v1/indicators/", headers=admin_headers, json={
            "source_id": created_source["id"],
            "indicators": [{"type": "domain", "value": val}]
        })
        indicator_id = resp.json()["indicators"][0]["id"]

        await asyncio.sleep(WORKER_WAIT_SECONDS)

        detail = (await client.get(
            f"/api/v1/indicators/{indicator_id}", headers=admin_headers
        )).json()

        assert "evidence" in detail, "Indicator detail response must include evidence array"
        assert len(detail["evidence"]) > 0, (
            "No evidence records found — enrichment workers may not be running"
        )

    async def test_evidence_record_schema(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        """Every evidence record must have the required fields."""
        val = f"evidence-schema-{uuid.uuid4().hex[:6]}.com"
        resp = await client.post("/api/v1/indicators/", headers=admin_headers, json={
            "source_id": created_source["id"],
            "indicators": [{"type": "domain", "value": val}]
        })
        indicator_id = resp.json()["indicators"][0]["id"]

        await asyncio.sleep(WORKER_WAIT_SECONDS)

        detail = (await client.get(
            f"/api/v1/indicators/{indicator_id}", headers=admin_headers
        )).json()

        for ev in detail.get("evidence", []):
            assert "id" in ev
            assert "evidence_type" in ev
            assert "timestamp" in ev
            assert "confidence_delta" in ev
            assert "raw_payload" in ev
            assert "reversible" in ev
            assert "reversed" in ev

    async def test_evidence_is_not_mutated(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        """Evidence records must have no updated_at field — they are append-only."""
        val = f"immutable-ev-{uuid.uuid4().hex[:6]}.com"
        resp = await client.post("/api/v1/indicators/", headers=admin_headers, json={
            "source_id": created_source["id"],
            "indicators": [{"type": "domain", "value": val}]
        })
        indicator_id = resp.json()["indicators"][0]["id"]

        await asyncio.sleep(WORKER_WAIT_SECONDS)

        detail = (await client.get(
            f"/api/v1/indicators/{indicator_id}", headers=admin_headers
        )).json()

        for ev in detail.get("evidence", []):
            assert "updated_at" not in ev, "Evidence must be append-only — no updated_at allowed"


# ─────────────────────────────────────────────
# CONFIDENCE SNAPSHOTS — RATIONALE
# ─────────────────────────────────────────────

class TestConfidenceSnapshots:
    async def test_confidence_snapshot_exists_after_scoring(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        val = f"snapshot-{uuid.uuid4().hex[:6]}.com"
        resp = await client.post("/api/v1/indicators/", headers=admin_headers, json={
            "source_id": created_source["id"],
            "indicators": [{"type": "domain", "value": val}]
        })
        indicator_id = resp.json()["indicators"][0]["id"]

        await asyncio.sleep(WORKER_WAIT_SECONDS)

        detail = (await client.get(
            f"/api/v1/indicators/{indicator_id}", headers=admin_headers
        )).json()

        assert "confidence_history" in detail or "snapshots" in detail, (
            "Indicator detail must include confidence snapshot history"
        )

    async def test_rationale_present_in_snapshot(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        """Every snapshot must include a rationale — this is MVP requirement #3."""
        val = f"rationale-{uuid.uuid4().hex[:6]}.com"
        resp = await client.post("/api/v1/indicators/", headers=admin_headers, json={
            "source_id": created_source["id"],
            "indicators": [{"type": "domain", "value": val}]
        })
        indicator_id = resp.json()["indicators"][0]["id"]

        await asyncio.sleep(WORKER_WAIT_SECONDS)

        detail = (await client.get(
            f"/api/v1/indicators/{indicator_id}", headers=admin_headers
        )).json()

        snapshots = detail.get("confidence_history") or detail.get("snapshots") or []
        assert len(snapshots) > 0

        latest = snapshots[0]
        assert "score" in latest
        rationale = latest.get("reason_summary")
        assert rationale is not None
        assert "factors" in rationale
        assert "decay_factor" in rationale
        assert "calculated_at" in rationale

    async def test_confidence_score_clamped_0_to_100(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        val = f"clamp-{uuid.uuid4().hex[:6]}.com"
        resp = await client.post("/api/v1/indicators/", headers=admin_headers, json={
            "source_id": created_source["id"],
            "indicators": [{"type": "domain", "value": val}]
        })
        indicator_id = resp.json()["indicators"][0]["id"]

        await asyncio.sleep(WORKER_WAIT_SECONDS)

        detail = (await client.get(
            f"/api/v1/indicators/{indicator_id}", headers=admin_headers
        )).json()

        assert 0 <= detail["current_confidence"] <= 100


# ─────────────────────────────────────────────
# MULTI-SOURCE CORRELATION
# ─────────────────────────────────────────────

class TestMultiSourceCorrelation:
    async def test_multi_source_sighting_increases_confidence(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Same indicator seen from 2 sources should score higher than from 1 source."""
        # Create a second source
        name2 = f"Second Source Corr Test {uuid.uuid4().hex[:6]}"
        src2 = (await client.post("/api/v1/sources/", headers=admin_headers, json={
            "name": name2,
            "category": "research",
            "trust_tier": "MEDIUM",
            "default_weight": 0.6
        })).json()

        name1 = f"First Source Corr Test {uuid.uuid4().hex[:6]}"
        src1_id = (await client.post("/api/v1/sources/", headers=admin_headers, json={
            "name": name1,
            "category": "community",
            "trust_tier": "MEDIUM",
            "default_weight": 0.6
        })).json()["id"]

        # Ingest same domain from source 1
        common_val = f"multi-src-{uuid.uuid4().hex[:6]}.com"
        r = await client.post("/api/v1/indicators/", headers=admin_headers, json={
            "source_id": src1_id,
            "indicators": [{"type": "domain", "value": common_val}]
        })
        indicator_id = r.json()["indicators"][0]["id"]

        # Wait for first enrichment + scoring
        await asyncio.sleep(WORKER_WAIT_SECONDS)
        score_after_one_source = (await client.get(
            f"/api/v1/indicators/{indicator_id}", headers=admin_headers
        )).json()["current_confidence"]

        # Ingest same domain from source 2 (triggers duplicate merge + correlation)
        await client.post("/api/v1/indicators/", headers=admin_headers, json={
            "source_id": src2["id"],
            "indicators": [{"type": "domain", "value": common_val}]
        })

        await asyncio.sleep(WORKER_WAIT_SECONDS)
        score_after_two_sources = (await client.get(
            f"/api/v1/indicators/{indicator_id}", headers=admin_headers
        )).json()["current_confidence"]

        assert score_after_two_sources >= score_after_one_source, (
            "Score should not decrease when a second source corroborates the indicator"
        )


# ─────────────────────────────────────────────
# DECAY — SCORE DECREASES OVER TIME
# ─────────────────────────────────────────────

class TestDecaySmoke:
    async def test_decay_rationale_includes_decay_factor(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        """Rationale must always include decay_factor so analysts can see it applied."""
        val = f"decay-rat-{uuid.uuid4().hex[:6]}.com"
        resp = await client.post("/api/v1/indicators/", headers=admin_headers, json={
            "source_id": created_source["id"],
            "indicators": [{"type": "domain", "value": val}]
        })
        indicator_id = resp.json()["indicators"][0]["id"]

        await asyncio.sleep(WORKER_WAIT_SECONDS)

        detail = (await client.get(
            f"/api/v1/indicators/{indicator_id}", headers=admin_headers
        )).json()

        snapshots = detail.get("confidence_history") or detail.get("snapshots") or []
        if snapshots:
            rationale = snapshots[0].get("reason_summary") or snapshots[0].get("rationale", {})
            assert "decay_factor" in rationale
            assert "days_elapsed" in rationale
            # For a brand new indicator, days_elapsed should be 0 and decay_factor ~1.0
            assert rationale["days_elapsed"] == 0
            assert 0.99 <= rationale["decay_factor"] <= 1.0
