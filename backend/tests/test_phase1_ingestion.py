"""
Phase 1 Tests — Indicator Ingestion
Covers POST /api/v1/indicators/
Tests: validation, normalization, deduplication, partial ingestion, file upload.
"""
import io
import uuid
import pytest
from httpx import AsyncClient


# ─────────────────────────────────────────────
# HAPPY PATH — VALID INDICATORS
# ─────────────────────────────────────────────

class TestIngestHappyPath:
    async def test_ingest_single_ipv4(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        ip = f"1.2.3.{uuid.uuid4().int % 255}"
        resp = await client.post("/api/v1/indicators", headers=admin_headers, json={
            "source_id": created_source["id"],
            "indicators": [{"type": "ipv4", "value": ip}]
        })
        assert resp.status_code in (200, 202)
        body = resp.json()
        assert body["ingested"] == 1
        assert body["errors"] == 0
        assert body["duplicates"] == 0

    async def test_ingest_all_valid_types(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        u = uuid.uuid4().hex[:6]
        resp = await client.post("/api/v1/indicators", headers=admin_headers, json={
            "source_id": created_source["id"],
            "indicators": [
                {"type": "ipv4",   "value": f"{uuid.uuid4().int % 255}.{uuid.uuid4().int % 255}.{uuid.uuid4().int % 255}.{uuid.uuid4().int % 255}"},
                {"type": "ipv6",   "value": f"2001:db8::{uuid.uuid4().hex[:4]}:{uuid.uuid4().hex[:4]}"},
                {"type": "domain", "value": f"malicious-{uuid.uuid4().hex}.com"},
                {"type": "url",    "value": f"http://evil-{uuid.uuid4().hex}.com/payload.exe"},
                {"type": "md5",    "value": uuid.uuid4().hex},
                {"type": "sha1",   "value": (uuid.uuid4().hex + uuid.uuid4().hex)[:40]},
                {"type": "sha256", "value": (uuid.uuid4().hex + uuid.uuid4().hex)[:64]},
            ]
        })
        body = resp.json()
        assert body["ingested"] == 7
        assert body["errors"] == 0

    async def test_response_contains_indicator_objects(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        ip = f"192.168.100.{uuid.uuid4().int % 255}"
        resp = await client.post("/api/v1/indicators", headers=admin_headers, json={
            "source_id": created_source["id"],
            "indicators": [{"type": "ipv4", "value": ip}]
        })
        body = resp.json()
        assert "indicators" in body
        assert len(body["indicators"]) >= 1

        ind = body["indicators"][0]
        required_fields = {"id", "type", "value", "status", "current_confidence",
                           "first_seen", "last_seen", "ttl"}
        assert required_fields.issubset(ind.keys())

    async def test_new_indicator_has_zero_confidence(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        """Initial confidence must be 0 — scoring is async, never set at ingestion."""
        ip = f"44.44.44.{uuid.uuid4().int % 255}"
        resp = await client.post("/api/v1/indicators", headers=admin_headers, json={
            "source_id": created_source["id"],
            "indicators": [{"type": "ipv4", "value": ip}]
        })
        indicator = resp.json()["indicators"][0]
        assert indicator["current_confidence"] == 0

    async def test_new_indicator_status_is_active(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        domain = f"new-active-{uuid.uuid4().hex[:6]}.com"
        resp = await client.post("/api/v1/indicators", headers=admin_headers, json={
            "source_id": created_source["id"],
            "indicators": [{"type": "domain", "value": domain}]
        })
        indicator = resp.json()["indicators"][0]
        assert indicator["status"] == "ACTIVE"


# ─────────────────────────────────────────────
# DEDUPLICATION
# ─────────────────────────────────────────────

class TestDeduplication:
    async def test_duplicate_same_source_counted(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        ip = f"77.77.77.{uuid.uuid4().int % 255}"
        payload = {
            "source_id": created_source["id"],
            "indicators": [{"type": "ipv4", "value": ip}]
        }
        await client.post("/api/v1/indicators", headers=admin_headers, json=payload)
        resp2 = await client.post("/api/v1/indicators", headers=admin_headers, json=payload)
        body = resp2.json()
        assert body["duplicates"] == 1
        assert body["ingested"] == 0

    async def test_duplicate_does_not_create_new_row(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        """Same indicator submitted twice = still one record in DB."""
        ip = f"88.88.88.{uuid.uuid4().int % 255}"
        payload = {
            "source_id": created_source["id"],
            "indicators": [{"type": "ipv4", "value": ip}]
        }
        r1 = await client.post("/api/v1/indicators", headers=admin_headers, json=payload)
        r2 = await client.post("/api/v1/indicators", headers=admin_headers, json=payload)

        id_first = r1.json()["indicators"][0]["id"]
        id_second = r2.json()["indicators"][0]["id"]
        assert id_first == id_second   # same record, not a new one

    async def test_mixed_new_and_duplicate(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        # First: ingest one indicator
        ip = f"99.99.99.{uuid.uuid4().int % 255}"
        ip_new = f"100.100.100.{uuid.uuid4().int % 255}"
        await client.post("/api/v1/indicators", headers=admin_headers, json={
            "source_id": created_source["id"],
            "indicators": [{"type": "ipv4", "value": ip}]
        })
        # Second: ingest same + one new
        resp = await client.post("/api/v1/indicators", headers=admin_headers, json={
            "source_id": created_source["id"],
            "indicators": [
                {"type": "ipv4", "value": ip},   # duplicate
                {"type": "ipv4", "value": ip_new} # new
            ]
        })
        body = resp.json()
        assert body["ingested"] == 1
        assert body["duplicates"] == 1
        assert body["errors"] == 0


# ─────────────────────────────────────────────
# NORMALIZATION
# ─────────────────────────────────────────────

class TestNormalization:
    async def test_url_defang_hxxp_treated_as_duplicate(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        """hxxp://evil.com/path and http://evil.com/path = same canonical indicator."""
        source_id = created_source["id"]
        await client.post("/api/v1/indicators", headers=admin_headers, json={
            "source_id": source_id,
            "indicators": [{"type": "url", "value": "http://defang-test.com/path"}]
        })
        resp = await client.post("/api/v1/indicators", headers=admin_headers, json={
            "source_id": source_id,
            "indicators": [{"type": "url", "value": "hxxp://defang-test.com/path"}]
        })
        assert resp.json()["duplicates"] == 1

    async def test_url_defang_brackets_treated_as_duplicate(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        source_id = created_source["id"]
        u = uuid.uuid4().hex[:6]
        await client.post("/api/v1/indicators", headers=admin_headers, json={
            "source_id": source_id,
            "indicators": [{"type": "url", "value": f"http://bracket-{u}.com/gate"}]
        })
        resp = await client.post("/api/v1/indicators", headers=admin_headers, json={
            "source_id": source_id,
            "indicators": [{"type": "url", "value": f"hxxp://bracket-{u}[.]com/gate"}]
        })
        assert resp.json()["duplicates"] == 1

    async def test_domain_uppercased_treated_as_duplicate(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        source_id = created_source["id"]
        await client.post("/api/v1/indicators", headers=admin_headers, json={
            "source_id": source_id,
            "indicators": [{"type": "domain", "value": "evil-domain.com"}]
        })
        resp = await client.post("/api/v1/indicators", headers=admin_headers, json={
            "source_id": source_id,
            "indicators": [{"type": "domain", "value": "EVIL-DOMAIN.COM"}]
        })
        assert resp.json()["duplicates"] == 1

    async def test_url_http_and_https_same_canonical(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        source_id = created_source["id"]
        await client.post("/api/v1/indicators", headers=admin_headers, json={
            "source_id": source_id,
            "indicators": [{"type": "url", "value": "http://schema-test.com/path"}]
        })
        resp = await client.post("/api/v1/indicators", headers=admin_headers, json={
            "source_id": source_id,
            "indicators": [{"type": "url", "value": "https://schema-test.com/path"}]
        })
        assert resp.json()["duplicates"] == 1

    async def test_sha256_uppercased_treated_as_duplicate(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        source_id = created_source["id"]
        hash_lower = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        hash_upper = hash_lower.upper()
        await client.post("/api/v1/indicators", headers=admin_headers, json={
            "source_id": source_id,
            "indicators": [{"type": "sha256", "value": hash_lower}]
        })
        resp = await client.post("/api/v1/indicators", headers=admin_headers, json={
            "source_id": source_id,
            "indicators": [{"type": "sha256", "value": hash_upper}]
        })
        assert resp.json()["duplicates"] == 1

    async def test_url_preserves_full_path(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        """Path must not be stripped — /gate.php?id=1 must be stored."""
        resp = await client.post("/api/v1/indicators", headers=admin_headers, json={
            "source_id": created_source["id"],
            "indicators": [{"type": "url", "value": "http://c2server.com/gate.php?id=999"}]
        })
        stored_value = resp.json()["indicators"][0]["value"]
        assert "/gate.php" in stored_value
        assert "id=999" in stored_value

    async def test_url_with_port_is_distinct_indicator(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        """evil.com:8080/path and evil.com/path are different indicators."""
        source_id = created_source["id"]
        u = uuid.uuid4().hex[:6]
        r1 = await client.post("/api/v1/indicators", headers=admin_headers, json={
            "source_id": source_id,
            "indicators": [{"type": "url", "value": f"http://port-test-{u}.com/path"}]
        })
        r2 = await client.post("/api/v1/indicators", headers=admin_headers, json={
            "source_id": source_id,
            "indicators": [{"type": "url", "value": f"http://port-test-{u}.com:8080/path"}]
        })
        assert r2.json()["ingested"] == 1   # different indicator, not a duplicate
        assert r2.json()["duplicates"] == 0


# ─────────────────────────────────────────────
# VALIDATION — INVALID INPUTS
# ─────────────────────────────────────────────

class TestValidation:
    async def test_invalid_ipv4_reported_as_error(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        resp = await client.post("/api/v1/indicators", headers=admin_headers, json={
            "source_id": created_source["id"],
            "indicators": [{"type": "ipv4", "value": "999.999.999.999"}]
        })
        body = resp.json()
        assert body["errors"] == 1
        assert body["ingested"] == 0
        assert len(body["error_details"]) == 1
        assert body["error_details"][0]["is_valid"] is False

    async def test_invalid_md5_wrong_length(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        resp = await client.post("/api/v1/indicators", headers=admin_headers, json={
            "source_id": created_source["id"],
            "indicators": [{"type": "md5", "value": "tooshort"}]
        })
        assert resp.json()["errors"] == 1

    async def test_invalid_sha256_wrong_length(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        resp = await client.post("/api/v1/indicators", headers=admin_headers, json={
            "source_id": created_source["id"],
            "indicators": [{"type": "sha256", "value": "abc123"}]
        })
        assert resp.json()["errors"] == 1

    async def test_invalid_sha1_non_hex(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        resp = await client.post("/api/v1/indicators", headers=admin_headers, json={
            "source_id": created_source["id"],
            "indicators": [{"type": "sha1", "value": "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"}]
        })
        assert resp.json()["errors"] == 1

    async def test_partial_batch_processes_valid_rows(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        """Valid rows must be ingested even if some rows in the same batch fail."""
        # First: ingest one indicator
        ip = f"55.55.55.{uuid.uuid4().int % 255}"
        domain = f"valid-{uuid.uuid4().hex[:6]}.net"
        resp = await client.post("/api/v1/indicators", headers=admin_headers, json={
            "source_id": created_source["id"],
            "indicators": [
                {"type": "ipv4", "value": ip},                    # valid
                {"type": "ipv4", "value": "not_an_ip"},           # invalid
                {"type": "domain", "value": domain},              # valid
                {"type": "md5",  "value": "badhash"},             # invalid
            ]
        })
        body = resp.json()
        assert body["ingested"] == 2
        assert body["errors"] == 2
        assert resp.status_code in (200, 202)   # partial success is still 200/202

    async def test_error_detail_contains_raw_value(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        resp = await client.post("/api/v1/indicators", headers=admin_headers, json={
            "source_id": created_source["id"],
            "indicators": [{"type": "ipv4", "value": "bad-ip-value"}]
        })
        detail = resp.json()["error_details"][0]
        assert detail["raw"] == "bad-ip-value"
        assert "error" in detail
        assert detail["is_valid"] is False

    async def test_empty_indicators_list(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        resp = await client.post("/api/v1/indicators", headers=admin_headers, json={
            "source_id": created_source["id"],
            "indicators": []
        })
        body = resp.json()
        assert body["ingested"] == 0
        assert body["errors"] == 0

    async def test_nonexistent_source_id_returns_error(
        self, client: AsyncClient, admin_headers: dict
    ):
        resp = await client.post("/api/v1/indicators", headers=admin_headers, json={
            "source_id": "00000000-0000-0000-0000-000000000000",
            "indicators": [{"type": "ipv4", "value": "1.2.3.4"}]
        })
        assert resp.status_code in (400, 404, 422)


# ─────────────────────────────────────────────
# FILE UPLOAD — CSV / TXT
# ─────────────────────────────────────────────

class TestFileUpload:
    async def test_csv_upload_valid_rows(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        ip = f"11.22.33.{uuid.uuid4().int % 255}"
        domain = f"csv-up-{uuid.uuid4().hex[:6]}.com"
        csv_content = f"type,value\nipv4,{ip}\ndomain,{domain}\n".encode()
        resp = await client.post("/api/v1/indicators",
            headers=admin_headers,
            data={"source_id": created_source["id"]},
            files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
        )
        body = resp.json()
        assert body["ingested"] == 2
        assert body["errors"] == 0

    async def test_csv_upload_mixed_valid_invalid(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        ip = f"{uuid.uuid4().int % 255}.{uuid.uuid4().int % 255}.{uuid.uuid4().int % 255}.{uuid.uuid4().int % 255}"
        domain = f"csv-mixed-{uuid.uuid4().hex[:6]}.com"
        csv_content = (
            "type,value\n"
            f"ipv4,{ip}\n"
            "ipv4,not_valid_ip\n"
            f"domain,{domain}\n"
        ).encode('utf-8')
        resp = await client.post("/api/v1/indicators",
            headers=admin_headers,
            data={"source_id": created_source["id"]},
            files={"file": ("mixed.csv", io.BytesIO(csv_content), "text/csv")}
        )
        body = resp.json()
        assert body["ingested"] == 2
        assert body["errors"] == 1

    async def test_txt_upload_one_per_line(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        ip1 = f"{uuid.uuid4().int % 255}.{uuid.uuid4().int % 255}.{uuid.uuid4().int % 255}.{uuid.uuid4().int % 255}"
        ip2 = f"{uuid.uuid4().int % 255}.{uuid.uuid4().int % 255}.{uuid.uuid4().int % 255}.{uuid.uuid4().int % 255}"
        txt_content = f"{ip1}\n{ip2}\nbad-line!!!\n".encode('utf-8')
        resp = await client.post("/api/v1/indicators",
            headers=admin_headers,
            data={"source_id": created_source["id"]},
            files={"file": ("indicators.txt", io.BytesIO(txt_content), "text/plain")}
        )
        body = resp.json()
        assert body["ingested"] == 2    # the two valid IPs

    async def test_csv_upload_returns_same_schema_as_json(
        self, client: AsyncClient, admin_headers: dict, created_source: dict
    ):
        """CSV and JSON ingestion must produce identical response shapes."""
        csv_content = b"type,value\nipv4,33.44.55.66\n"
        resp = await client.post("/api/v1/indicators",
            headers=admin_headers,
            data={"source_id": created_source["id"]},
            files={"file": ("schema.csv", io.BytesIO(csv_content), "text/csv")}
        )
        body = resp.json()
        assert "ingested" in body
        assert "duplicates" in body
        assert "errors" in body
        assert "error_details" in body
        assert "indicators" in body
