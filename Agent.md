# AGENT.md — Threat Intelligence Platform (TIP)

# Read this file completely before writing a single line of code.

# Re-read the relevant sections before starting each task.

---

## 0. What This File Is

This is the authoritative instruction set for every LLM agent session working on this codebase.
It contains project context, architectural decisions, coding rules, and anti-drift guardrails.

**If you are unsure about anything, the answer is in this file or in the SRS.
Do not invent. Do not assume. Do not add features not in the spec.**

---

## 1. Project Overview

**Product:** Threat Intelligence Platform (TIP) — MVP
**Client:** Security Shark LLP
**Builder:** Bitwise (v1.2, March 2026)
**Purpose:** Ingest raw threat indicators from untrusted external sources, enrich them with
independent evidence, correlate across sources, dynamically score/decay confidence, and
provide human-explainable justification for every risk decision.

### The 5 MVP objectives (acceptance gates)

1. Confidence scores change meaningfully over time
2. Indicators expire automatically without reaffirmation
3. Analysts can explain why an indicator is high or low risk (from the UI alone)
4. Raw feeds become more actionable after enrichment
5. No automated blocking occurs without human approval

**Every feature you build must serve at least one of these five objectives.
If it doesn't, it is out of scope — do not build it.**

### Explicitly OUT of scope for MVP (never implement these)

- Threat actor attribution
- Campaign modeling
- Automated blocking or enforcement actions
- Full STIX internal data model
- TAXII client/server
- Machine learning or AI-based classification
- Internal customer telemetry ingestion
- Executive dashboards

---

## 2. Tech Stack (Locked — Do Not Change Without Discussion)

### Backend

| Component      | Choice                          | Version          |
| -------------- | ------------------------------- | ---------------- |
| Language       | Python                          | 3.12             |
| API framework  | FastAPI                         | latest stable    |
| ORM            | SQLAlchemy                      | 2.x (async)      |
| Migrations     | Alembic                         | latest           |
| Validation     | Pydantic                        | v2               |
| Task queue     | Celery                          | 5.x              |
| Message broker | Redis                           | 7                |
| Scheduler      | Celery Beat                     | (same as Celery) |
| HTTP client    | httpx                           | latest (async)   |
| Auth           | python-jose + passlib           | latest           |
| Linting        | Ruff                            | latest           |
| Type checking  | mypy                            | latest (strict)  |
| Testing        | pytest + pytest-asyncio + httpx | latest           |
| Redis mocking  | fakeredis                       | latest           |

### Database

| Component     | Choice                        |
| ------------- | ----------------------------- |
| Primary store | PostgreSQL 15                 |
| Schema        | See Section 5 — never deviate |
| Indexing      | See Section 5.4               |

### Frontend

| Component    | Choice                           |
| ------------ | -------------------------------- |
| Framework    | React 18 + TypeScript            |
| Build tool   | Vite                             |
| Server state | TanStack Query (React Query v5)  |
| Routing      | React Router v6                  |
| Styling      | Tailwind CSS                     |
| Charts       | Recharts                         |
| HTTP         | Axios (with interceptor for JWT) |

### Infrastructure

| Component       | Choice                                                 |
| --------------- | ------------------------------------------------------ |
| Dev environment | Docker Compose                                         |
| Container names | tip-api, tip-postgres, tip-redis, tip-worker, tip-beat |
| CI              | GitHub Actions                                         |
| Reverse proxy   | nginx (TLS termination)                                |
| Rate limiting   | slowapi (FastAPI)                                      |

---

## 3. Repository Structure

```
/
├── backend/
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── indicators.py
│   │   │   │   ├── sources.py
│   │   │   │   ├── export.py
│   │   │   │   └── auth.py
│   │   ├── core/
│   │   │   ├── config.py          # Settings via pydantic-settings
│   │   │   ├── security.py        # JWT, password hashing
│   │   │   └── dependencies.py    # FastAPI Depends functions
│   │   ├── db/
│   │   │   ├── base.py            # SQLAlchemy Base
│   │   │   └── session.py         # Async engine + session factory
│   │   ├── models/                # SQLAlchemy ORM models (one file per table)
│   │   │   ├── indicator.py
│   │   │   ├── source.py
│   │   │   ├── evidence.py
│   │   │   ├── confidence_snapshot.py
│   │   │   ├── user.py
│   │   │   └── audit_log.py
│   │   ├── schemas/               # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── ingestion/
│   │   │   │   ├── validator.py
│   │   │   │   └── normalizer.py
│   │   │   ├── enrichment/
│   │   │   │   ├── base.py        # BaseEnricher abstract class
│   │   │   │   ├── factory.py     # EnrichmentEngineFactory
│   │   │   │   ├── whois.py
│   │   │   │   ├── passive_dns.py
│   │   │   │   ├── asn.py
│   │   │   │   ├── ssl_cert.py
│   │   │   │   └── behavioral.py
│   │   │   ├── correlation/
│   │   │   │   └── engine.py
│   │   │   └── scoring/
│   │   │       ├── engine.py
│   │   │       ├── decay.py
│   │   │       └── rationale.py
│   │   ├── workers/               # Celery task definitions
│   │   │   ├── celery_app.py
│   │   │   ├── enrichment_worker.py
│   │   │   ├── correlation_worker.py
│   │   │   ├── scoring_worker.py
│   │   │   └── decay_scheduler.py
│   │   └── main.py
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── conftest.py
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/               # Axios query functions (one file per resource)
│   │   ├── components/        # Reusable UI components
│   │   ├── pages/             # Route-level page components
│   │   ├── hooks/             # Custom React hooks
│   │   └── types/             # TypeScript interfaces (mirror backend schemas)
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── nginx/
│   └── nginx.conf
├── .github/
│   └── workflows/
│       └── ci.yml
└── AGENT.md                   # This file
```

---

## 4. Data Model (Canonical — Do Not Modify Schema Without Migration)

This is the single source of truth for all table shapes.
Every SQLAlchemy model, every Pydantic schema, every test fixture must match this exactly.

### 4.1 SOURCES

```sql
id              UUID        PK DEFAULT gen_random_uuid()
name            VARCHAR(255) NOT NULL UNIQUE
category        ENUM('community','research','commercial','internal') NOT NULL
trust_tier      ENUM('LOW','MEDIUM','HIGH') NOT NULL
default_weight  NUMERIC(3,2) NOT NULL  -- 0.3 / 0.6 / 1.0
intent_description TEXT
pull_url        VARCHAR(2048)           -- nullable, for scheduled HTTP feeds
pull_schedule   VARCHAR(100)            -- cron expression, nullable
is_active       BOOLEAN NOT NULL DEFAULT true
created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

### 4.2 INDICATORS

```sql
id                  UUID        PK DEFAULT gen_random_uuid()
type                ENUM('IPV4','IPV6','DOMAIN','URL','MD5','SHA1','SHA256') NOT NULL
value               VARCHAR(2048) NOT NULL
first_seen          TIMESTAMPTZ NOT NULL DEFAULT NOW()
last_seen           TIMESTAMPTZ NOT NULL DEFAULT NOW()
ttl                 TIMESTAMPTZ NOT NULL              -- expiry timestamp
status              ENUM('ACTIVE','EXPIRED','REVOKED') NOT NULL DEFAULT 'ACTIVE'
current_confidence  NUMERIC(5,2) NOT NULL DEFAULT 0
UNIQUE(type, value)
```

### 4.3 INDICATOR_SOURCES (junction table)

```sql
id              UUID        PK DEFAULT gen_random_uuid()
indicator_id    UUID        FK → INDICATORS NOT NULL
source_id       UUID        FK → SOURCES NOT NULL
first_reported_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
last_reported_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
UNIQUE(indicator_id, source_id)
```

### 4.4 EVIDENCE ← APPEND-ONLY. Never UPDATE or DELETE rows.

```sql
id                UUID        PK DEFAULT gen_random_uuid()
indicator_id      UUID        FK → INDICATORS NOT NULL
source_id         UUID        FK → SOURCES nullable  -- null for system-generated evidence
evidence_type     ENUM('WHOIS','PASSIVE_DNS','ASN','SSL_CERT','CORRELATION_INFRA',
                        'CORRELATION_SSL','MULTI_SOURCE_SIGHTING','ANALYST_NOTE',
                        'ANALYST_ADJUSTMENT','REVOCATION') NOT NULL
timestamp         TIMESTAMPTZ NOT NULL DEFAULT NOW()
confidence_delta  NUMERIC(5,2) NOT NULL DEFAULT 0
raw_payload       JSONB NOT NULL
reversible        BOOLEAN NOT NULL DEFAULT false
reversed          BOOLEAN NOT NULL DEFAULT false
reversed_at       TIMESTAMPTZ nullable
reversed_by       UUID FK → USERS nullable
-- NO updated_at column. Immutability is structural.
```

### 4.5 CONFIDENCE_SNAPSHOTS ← APPEND-ONLY. Never UPDATE or DELETE rows.

```sql
id              UUID        PK DEFAULT gen_random_uuid()
indicator_id    UUID        FK → INDICATORS NOT NULL
score           NUMERIC(5,2) NOT NULL               -- 0.00 to 100.00
calculated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
reason_summary  JSONB NOT NULL                      -- full rationale (see Section 7)
trigger         VARCHAR(100) NOT NULL               -- 'evidence.created' | 'correlation.created' | 'decay.job'
```

### 4.6 USERS

```sql
id              UUID        PK DEFAULT gen_random_uuid()
username        VARCHAR(100) NOT NULL UNIQUE
email           VARCHAR(255) NOT NULL UNIQUE
password_hash   VARCHAR(255) NOT NULL
is_active       BOOLEAN NOT NULL DEFAULT true
created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
last_login      TIMESTAMPTZ nullable
```

### 4.7 ROLES

```sql
id              UUID        PK DEFAULT gen_random_uuid()
name            ENUM('ADMIN','ANALYST','API_CONSUMER') NOT NULL UNIQUE
description     TEXT
permissions     JSONB NOT NULL
```

### 4.8 USER_ROLES (junction table)

```sql
id              UUID        PK DEFAULT gen_random_uuid()
user_id         UUID        FK → USERS NOT NULL
role_id         UUID        FK → ROLES NOT NULL
granted_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
granted_by      UUID        FK → USERS NOT NULL
UNIQUE(user_id, role_id)
```

### 4.9 AUDIT_LOGS

```sql
id              UUID        PK DEFAULT gen_random_uuid()
user_id         UUID        FK → USERS nullable     -- null for system actions
action          VARCHAR(100) NOT NULL
entity_type     VARCHAR(100) NOT NULL
entity_id       UUID NOT NULL
details         JSONB NOT NULL
ip_address      INET nullable
is_active       BOOLEAN NOT NULL DEFAULT true
timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

### 4.10 Required Database Indexes

```sql
-- List queries (most common)
CREATE INDEX idx_indicators_status_confidence ON indicators(status, current_confidence DESC);
CREATE INDEX idx_indicators_type ON indicators(type);
CREATE INDEX idx_indicators_last_seen ON indicators(last_seen DESC);

-- Evidence retrieval (hot path for scoring)
CREATE INDEX idx_evidence_indicator_id ON evidence(indicator_id);
CREATE INDEX idx_evidence_indicator_timestamp ON evidence(indicator_id, timestamp DESC);
CREATE INDEX idx_evidence_type ON evidence(evidence_type);

-- Correlation queries
CREATE INDEX idx_evidence_asn ON evidence USING GIN(raw_payload) WHERE evidence_type = 'ASN';
CREATE INDEX idx_evidence_ssl ON evidence USING GIN(raw_payload) WHERE evidence_type = 'SSL_CERT';

-- Snapshot retrieval
CREATE INDEX idx_snapshots_indicator_calculated ON confidence_snapshots(indicator_id, calculated_at DESC);

-- Audit queries
CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_user ON audit_logs(user_id, timestamp DESC);
```

---

## 5. Trust Tier Weight Map (Hardcoded — Do Not Change)

```python
TRUST_WEIGHT_MAP = {
    "LOW":    0.3,
    "MEDIUM": 0.6,
    "HIGH":   1.0,
}
```

---

## 6. Confidence Scoring Formula (Exact — Do Not Deviate)

This is the deterministic scoring algorithm. Every implementation must match this exactly.
Tests will verify the math independently.

```python
import math
from decimal import Decimal

DECAY_LAMBDA = 0.05          # configurable via env var TIP_DECAY_LAMBDA
ENRICHMENT_DEPTH_MULTIPLIER = 2
MULTI_SOURCE_DELTA_PER_SOURCE = 3
CORRELATION_INFRA_DELTA = 5
CORRELATION_SSL_DELTA = 8

def compute_confidence(
    evidence_records: list[Evidence],
    last_seen: datetime,
    analyst_adjustments: list[Evidence],
) -> tuple[float, dict]:

    base_score = 0.0
    factors = []

    # 1. Weighted evidence sum
    for ev in evidence_records:
        if ev.reversed:
            continue  # reversed evidence contributes nothing
        weight = TRUST_WEIGHT_MAP[ev.source.trust_tier] if ev.source else 1.0
        contribution = float(ev.confidence_delta) * weight
        base_score += contribution
        factors.append({
            "type": ev.evidence_type,
            "delta": float(ev.confidence_delta),
            "weight": weight,
            "contribution": contribution,
            "evidence_id": str(ev.id),
            "source_name": ev.source.name if ev.source else "system",
        })

    # 2. Enrichment depth bonus
    distinct_evidence_types = len(set(
        ev.evidence_type for ev in evidence_records
        if not ev.reversed and ev.evidence_type not in (
            'ANALYST_NOTE', 'ANALYST_ADJUSTMENT', 'REVOCATION',
            'CORRELATION_INFRA', 'CORRELATION_SSL', 'MULTI_SOURCE_SIGHTING'
        )
    ))
    enrichment_depth_bonus = distinct_evidence_types * ENRICHMENT_DEPTH_MULTIPLIER

    # 3. Correlation bonus (already in base_score via evidence_delta, but track separately)
    correlation_bonus = sum(
        float(ev.confidence_delta) for ev in evidence_records
        if not ev.reversed and ev.evidence_type in (
            'CORRELATION_INFRA', 'CORRELATION_SSL', 'MULTI_SOURCE_SIGHTING'
        )
    )

    # 4. Analyst adjustments
    analyst_adj = sum(
        float(ev.confidence_delta) for ev in analyst_adjustments
        if not ev.reversed
    )

    weighted_sum = base_score + enrichment_depth_bonus + analyst_adj

    # 5. Exponential time decay
    days_elapsed = (datetime.utcnow() - last_seen).days
    decay_factor = math.exp(-DECAY_LAMBDA * days_elapsed)
    decayed_score = weighted_sum * decay_factor

    # 6. Clamp
    final_score = max(0.0, min(100.0, decayed_score))

    rationale = {
        "score": round(final_score, 2),
        "base_score": round(base_score, 2),
        "enrichment_depth_bonus": enrichment_depth_bonus,
        "correlation_bonus": round(correlation_bonus, 2),
        "analyst_adjustment": round(analyst_adj, 2),
        "weighted_sum": round(weighted_sum, 2),
        "decay_factor": round(decay_factor, 4),
        "days_elapsed": days_elapsed,
        "calculated_at": datetime.utcnow().isoformat(),
        "factors": factors,
    }
    return final_score, rationale
```

**Auto-expiry rule:** After computing final_score, if `indicator.ttl < NOW()` AND `final_score < 10`,
set `indicator.status = 'EXPIRED'`. Do this in the same transaction as the snapshot INSERT.

---

## 7. Rationale JSON Schema (Every Snapshot Must Conform)

```json
{
  "score": 67.4,
  "base_score": 45.0,
  "enrichment_depth_bonus": 6,
  "correlation_bonus": 13.0,
  "analyst_adjustment": 0,
  "weighted_sum": 64.0,
  "decay_factor": 0.9512,
  "days_elapsed": 1,
  "calculated_at": "2026-03-20T14:30:00Z",
  "factors": [
    {
      "type": "WHOIS",
      "delta": 10,
      "weight": 0.6,
      "contribution": 6.0,
      "evidence_id": "uuid-here",
      "source_name": "AlienVault OTX"
    }
  ]
}
```

The analyst UI reads this JSON directly to render the "why" panel.
**Never store a score without its rationale. They are always written together in one INSERT.**

---

## 8. Redis Event Bus (Pub/Sub Channels)

These are the exact channel names. Do not rename them.

| Event                      | Channel               | Published by       | Consumed by                        |
| -------------------------- | --------------------- | ------------------ | ---------------------------------- |
| New indicator created      | `indicator.created`   | Ingestion service  | Enrichment worker                  |
| Duplicate indicator seen   | `indicator.updated`   | Ingestion service  | (logging only)                     |
| Enrichment result stored   | `evidence.created`    | Enrichment worker  | Correlation engine, Scoring worker |
| Correlation result stored  | `correlation.created` | Correlation engine | Scoring worker                     |
| Score meaningfully changed | `score.updated`       | Scoring worker     | (UI real-time, future)             |

**Event payload minimum shape:**

```json
{
  "indicator_id": "uuid",
  "indicator_type": "IPV4",
  "indicator_value": "1.2.3.4"
}
```

Always include all three fields in every event. Consumers may need any of them without a DB lookup.

---

## 9. API Conventions (All Endpoints Must Follow These)

### URL structure

```
/api/v1/{resource}                  # collection
/api/v1/{resource}/{id}             # item
/api/v1/{resource}/{id}/{sub}       # sub-resource
```

### Standard response envelope

```json
{
  "data": { ... },       // or [] for collections
  "meta": {              // only on paginated responses
    "total": 1000,
    "page": 1,
    "limit": 50,
    "pages": 20
  },
  "errors": []           // always present, empty on success
}
```

### Error response

```json
{
  "data": null,
  "errors": [
    {
      "code": "VALIDATION_ERROR",
      "field": "value",
      "message": "Invalid IPv4 format"
    }
  ]
}
```

### HTTP status codes used

| Code | When                                                                |
| ---- | ------------------------------------------------------------------- |
| 200  | Successful GET, PATCH                                               |
| 201  | Successful POST (resource created synchronously)                    |
| 202  | Accepted for async processing (indicator ingestion)                 |
| 400  | Validation failure                                                  |
| 401  | Missing or invalid token                                            |
| 403  | Valid token, insufficient role                                      |
| 404  | Resource not found                                                  |
| 409  | Conflict (duplicate source name, etc.)                              |
| 422  | Unprocessable entity (Pydantic parse failure)                       |
| 429  | Rate limit exceeded                                                 |
| 500  | Unhandled server error — log full traceback, return generic message |

### Pagination

All collection endpoints accept `?page=1&limit=50`. Max limit = 200. Default limit = 50.
Never return unbounded collections.

### Ingestion endpoint (special case)

`POST /api/v1/indicators` always returns 202, even if all rows fail validation.
The response body always contains counts: `{ingested, duplicates, errors, error_details}`.
Partial success is valid and expected.

---

## 10. Role Permission Matrix

| Endpoint                                 | ADMIN | ANALYST | API_CONSUMER |
| ---------------------------------------- | ----- | ------- | ------------ |
| POST /api/v1/sources                     | ✓     | ✗       | ✗            |
| GET /api/v1/sources                      | ✓     | ✓       | ✗            |
| POST /api/v1/indicators                  | ✓     | ✓       | ✓            |
| GET /api/v1/indicators                   | ✓     | ✓       | ✓            |
| GET /api/v1/indicators/{id}              | ✓     | ✓       | ✓            |
| POST /api/v1/indicators/{id}/notes       | ✓     | ✓       | ✗            |
| PATCH /api/v1/indicators/{id}/confidence | ✓     | ✓       | ✗            |
| PATCH /api/v1/indicators/{id}/revoke     | ✓     | ✓       | ✗            |
| PATCH /api/v1/indicators/{id}/ttl        | ✓     | ✓       | ✗            |
| GET /api/v1/export                       | ✓     | ✓       | ✓            |
| GET /api/v1/audit-logs                   | ✓     | ✗       | ✗            |
| POST /api/v1/auth/users                  | ✓     | ✗       | ✗            |

**High-confidence export rule:** GET /api/v1/export with `confidence_min >= 70` requires
the query param `approved=true`. If missing, return 403 with code `APPROVAL_REQUIRED`.

---

## 11. Enricher Specifications

### Confidence deltas by evidence type (hardcoded)

```python
EVIDENCE_CONFIDENCE_DELTAS = {
    "WHOIS":                  10,
    "PASSIVE_DNS":            8,
    "ASN":                    5,
    "SSL_CERT":               12,
    "CORRELATION_INFRA":      5,    # per correlated indicator
    "CORRELATION_SSL":        8,    # per shared fingerprint
    "MULTI_SOURCE_SIGHTING":  3,    # × source_count
    "ANALYST_NOTE":           0,    # notes don't change score
    "ANALYST_ADJUSTMENT":     0,    # delta comes from the analyst's input
    "REVOCATION":             -50,
}
```

### Enricher applicability matrix

```python
ENRICHER_TYPE_MAP = {
    "IPV4":   ["ASN", "PASSIVE_DNS"],
    "IPV6":   ["ASN", "PASSIVE_DNS"],
    "DOMAIN": ["WHOIS", "PASSIVE_DNS", "ASN", "SSL_CERT", "BEHAVIORAL"],
    "URL":    ["WHOIS", "PASSIVE_DNS", "ASN", "SSL_CERT", "BEHAVIORAL"],
    "MD5":    [],   # no external enrichment in MVP
    "SHA1":   [],
    "SHA256": [],
}
```

### Retry policy (all enrichers)

```python
MAX_RETRIES = 3
BACKOFF_MULTIPLIERS = [2, 4, 8]   # seconds before each retry
TIMEOUT_SECONDS = 10

# On failure after all retries:
# - Log: {"enricher": name, "indicator_id": id, "error": str(e), "attempts": 3}
# - Do NOT raise — return EnrichmentResult(success=False, error_message=str(e))
# - Do NOT insert a failed evidence row
# - Continue processing other enrichers
```

### Behavioral analyser flags (stored in raw_payload)

```python
{
    "is_short_lived_domain": bool,   # domain age < 30 days
    "infrastructure_reuse": bool,    # same ASN/IP seen in other indicators
    "suspicious_url_patterns": list[str],  # list of matched patterns
}
```

---

## 12. Coding Standards (Non-Negotiable)

### Python

**Async everywhere in FastAPI routes and services.**
Use `async def` for all route handlers, service methods that touch the DB or make HTTP calls.
Use `await` — never call sync code that blocks the event loop.

```python
# CORRECT
@router.get("/indicators/{indicator_id}")
async def get_indicator(
    indicator_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("ANALYST")),
) -> IndicatorDetailResponse:
    ...

# WRONG — never do this
@router.get("/indicators/{indicator_id}")
def get_indicator(indicator_id: UUID):   # sync handler in FastAPI = thread pool blocking
    ...
```

**All settings via pydantic-settings.**

```python
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    JWT_SECRET: str
    JWT_EXPIRE_MINUTES: int = 60
    DECAY_LAMBDA: float = 0.05
    class Config:
        env_file = ".env"

settings = Settings()
```

Never hardcode secrets, URLs, or tuneable values anywhere except config.py.

**Dependency injection pattern for DB sessions.**

```python
# app/db/session.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
```

**Transactions are explicit.**

```python
async def ingest_indicator(db: AsyncSession, ...) -> Indicator:
    async with db.begin():   # commit on success, rollback on exception
        indicator = Indicator(...)
        db.add(indicator)
        ...
    return indicator
```

**Never write raw SQL strings.** Use SQLAlchemy 2.0 style:

```python
# CORRECT
result = await db.execute(
    select(Indicator)
    .where(Indicator.type == indicator_type, Indicator.value == value)
)
# WRONG
result = await db.execute(f"SELECT * FROM indicators WHERE value = '{value}'")
```

**Type annotations are mandatory on all function signatures.**

```python
def compute_confidence(
    evidence_records: list[Evidence],
    last_seen: datetime,
) -> tuple[float, dict[str, Any]]:
```

**Pydantic v2 patterns.**

```python
from pydantic import BaseModel, field_validator, model_validator

class IndicatorCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # replaces orm_mode

    value: str
    type: IndicatorType
    source_id: UUID

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: str, info: FieldValidationInfo) -> str:
        ...
```

**Celery tasks are always idempotent.**
If a task runs twice with the same arguments, the result must be the same.
Use `ON CONFLICT DO NOTHING` or check-then-insert patterns.

**Logging format — always structured.**

```python
import structlog
logger = structlog.get_logger()

logger.info("enrichment_complete",
    indicator_id=str(indicator.id),
    enricher="WHOIS",
    evidence_id=str(evidence.id),
    confidence_delta=10,
)
# Never: logger.info(f"Enrichment complete for {indicator.id}")
```

### TypeScript / React

**No `any` types.** If you don't know the type, model it properly or use `unknown` with a guard.

**All API types are in `/src/types/`.** Mirror the backend Pydantic schemas.
When the backend schema changes, update the TypeScript type in the same commit.

**TanStack Query pattern.**

```typescript
// src/api/indicators.ts
export const getIndicator = async (id: string): Promise<IndicatorDetail> => {
  const { data } = await axios.get(`/api/v1/indicators/${id}`);
  return data.data;
};

// in component
const { data, isLoading, error } = useQuery({
  queryKey: ["indicator", id],
  queryFn: () => getIndicator(id),
});
```

**JWT in memory — never localStorage or sessionStorage.**

```typescript
let accessToken: string | null = null;
export const setToken = (t: string) => {
  accessToken = t;
};
export const getToken = () => accessToken;
// Axios interceptor reads getToken() on each request
```

**Error boundaries on all page-level components.**

---

## 13. Testing Requirements

### Coverage targets

| Layer                  | Minimum coverage                          |
| ---------------------- | ----------------------------------------- |
| Validator & Normalizer | 100% — every edge case                    |
| Scoring engine         | 100% — every formula branch               |
| Rationale builder      | 100% — output schema must always be valid |
| API route handlers     | 80%                                       |
| Enrichers              | 80% (with mocked external calls)          |
| Celery workers         | 70%                                       |

### Test anatomy

```python
# tests/unit/services/test_scoring.py
import pytest
from app.services.scoring.engine import compute_confidence

class TestConfidenceScoring:
    def test_zero_evidence_returns_zero(self):
        score, rationale = compute_confidence([], datetime.utcnow(), [])
        assert score == 0.0
        assert rationale["score"] == 0.0

    def test_decay_reduces_score_over_time(self):
        evidence = [build_evidence(delta=50, trust_tier="HIGH")]
        old_last_seen = datetime.utcnow() - timedelta(days=30)
        score_recent, _ = compute_confidence(evidence, datetime.utcnow(), [])
        score_old, _ = compute_confidence(evidence, old_last_seen, [])
        assert score_old < score_recent

    def test_reversed_evidence_contributes_nothing(self):
        ev = build_evidence(delta=50, trust_tier="HIGH", reversed=True)
        score, _ = compute_confidence([ev], datetime.utcnow(), [])
        assert score == 0.0

    def test_rationale_schema_always_valid(self):
        evidence = [build_evidence(delta=10, trust_tier="MEDIUM")]
        _, rationale = compute_confidence(evidence, datetime.utcnow(), [])
        assert "score" in rationale
        assert "factors" in rationale
        assert isinstance(rationale["factors"], list)
        assert "decay_factor" in rationale
```

### Integration test pattern

```python
# tests/integration/test_ingestion.py
@pytest.mark.asyncio
async def test_duplicate_indicator_merges_source(
    async_client: AsyncClient,
    db: AsyncSession,
    fake_redis: FakeRedis,
):
    source = await create_source(db, trust_tier="HIGH")
    # First ingestion
    await async_client.post("/api/v1/indicators", json={
        "source_id": str(source.id),
        "indicators": [{"type": "IPV4", "value": "1.2.3.4"}]
    })
    # Second ingestion of same indicator
    resp = await async_client.post("/api/v1/indicators", json={
        "source_id": str(source.id),
        "indicators": [{"type": "IPV4", "value": "1.2.3.4"}]
    })
    assert resp.json()["data"]["duplicates"] == 1
    # Verify only one indicator row exists
    result = await db.execute(select(func.count()).select_from(Indicator))
    assert result.scalar() == 1
    # Verify Redis event was published
    assert fake_redis.get_published("indicator.created") is not None
```

---

## 14. Anti-Drift Rules (Read Before Every Session)

These are the most common ways an LLM agent drifts on this project.
Check yourself against every rule before submitting code.

### ❌ Do not add features not in the SRS

If the SRS says "MVP excludes ML-based classification", do not add a scikit-learn classifier
"just to show how it could work". Build exactly what is specified. No more.

### ❌ Do not use synchronous SQLAlchemy in FastAPI routes

All DB access in API handlers must use `AsyncSession`. Using `Session` (sync) will block the
event loop under load and is a bug, not a style issue.

### ❌ Do not store secrets in code

No hardcoded passwords, JWT secrets, API keys, or database URLs anywhere except `.env` files
(which are gitignored) and the config.py Settings class.

### ❌ Do not mutate evidence rows

The EVIDENCE table is append-only. If you need to "undo" evidence, set `reversed=True`.
Never UPDATE or DELETE evidence. This is a core data integrity guarantee.

### ❌ Do not skip the rationale when inserting confidence snapshots

Every `INSERT INTO confidence_snapshots` must include the full rationale JSON.
A snapshot without a rationale violates MVP acceptance criteria #3.

### ❌ Do not return unbounded query results

Every endpoint that returns a list must have pagination. No exceptions.
`select(Indicator)` with no LIMIT is forbidden in production code.

### ❌ Do not auto-classify indicators at ingestion time

Ingestion inserts the raw indicator with `current_confidence = 0` and status `ACTIVE`.
The score is computed by the Scoring Engine asynchronously. Never set an initial score
based on the source's trust tier or any heuristic in the ingestion path.

### ❌ Do not let enricher failures crash the pipeline

Each enricher runs independently. One timeout does not stop other enrichers.
Use try/except in every enricher and return `EnrichmentResult(success=False, ...)`.

### ❌ Do not perform blocking HTTP calls inside Celery tasks without httpx async

If your Celery task needs HTTP, use `httpx.AsyncClient` inside an `asyncio.run()` wrapper
or configure Celery with the `gevent` pool. Never use `requests` (blocking).

### ❌ Do not put business logic in route handlers

Route handlers validate input, call a service function, return the response.
All logic lives in `app/services/`. A route handler should never contain SQL or scoring math.

### ❌ Do not skip audit logging for analyst actions

Every call to PATCH confidence, POST notes, PATCH revoke, GET export must insert
a row into AUDIT_LOGS. This is a compliance requirement, not optional.

---

## 15. Current Build State

Update this section at the end of every session.
# Phase 3 — Analyst UI [/] In progress

- [x] 3.1 Indicator query API
- [x] 3.2 Analyst action API endpoints
- [x] 3.3 React app scaffold + auth

```
Phase 0 — Foundation:        [x] Done
Phase 1 — Ingestion:         [x] Done
Phase 2 — Intelligence:      [x] Done
Phase 3 — Analyst UI:        [/] In progress
Phase 4 — Export/Hardening:  [ ] Not started

Last completed step: 3.3 — React app scaffold + auth
Last completed at:  2026-04-22
Next step:          3.4 — Indicator List UI (Phase 3)
Known issues:       None yet
```

---

## 16. Session Start Checklist

Before writing any code in a new session:

1. **Read sections 1, 3, 4 of this file** — purpose, structure, schema.
2. **Read the section of this file** that covers the component you are building.
3. **Identify which Phase/Step** you are on. Confirm with the user.
4. **State what you will build** in 2-3 sentences before writing code.
5. **State what tests you will write** before writing implementation.
6. **Confirm no out-of-scope work** will be introduced.
7. **Update Section 15** (Build State) at the end of the session.

---

## 17. Quick Reference — Key Numbers

| Parameter                        | Value                         |
| -------------------------------- | ----------------------------- |
| Confidence range                 | 0 – 100                       |
| Default initial confidence       | 0                             |
| Decay lambda (λ)                 | 0.05                          |
| Auto-expire threshold            | score < 10 AND TTL elapsed    |
| WHOIS timeout                    | 10 seconds                    |
| WHOIS max retries                | 3 (backoff: 2s, 4s, 8s)       |
| Ingestion latency SLA            | < 5 minutes                   |
| UI response time SLA             | < 2 seconds                   |
| Max API response limit           | 200 per page                  |
| Default API response limit       | 50 per page                   |
| Trust weight LOW                 | 0.3                           |
| Trust weight MEDIUM              | 0.6                           |
| Trust weight HIGH                | 1.0                           |
| Enrichment depth bonus           | distinct_enricher_count × 2   |
| Multi-source sighting delta      | source_count × 3              |
| High-confidence export threshold | ≥ 70 (requires approved=true) |
| Short-lived domain threshold     | age < 30 days                 |
| Score.updated publish threshold  | delta > 5 from last snapshot  |
