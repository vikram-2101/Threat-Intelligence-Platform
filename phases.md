Phase 0 — Foundation
Phase 1 — Ingestion
Phase 2 — Intelligence Engine
Phase 3 — Analyst UI
Phase 4 — Export & Hardening
Setup
0.1
Monorepo scaffold
Create /backend and /frontend directories. Set up pyproject.toml, Ruff, mypy, pre-commit hooks. GitHub Actions CI that runs lint + tests on every PR.
Python 3.12
Ruff
GitHub Actions
0.2
Docker Compose dev environment
Services: tip-api (FastAPI), tip-postgres (PostgreSQL 15), tip-redis (Redis 7), tip-worker (Celery), tip-beat (Celery Beat scheduler). All wired with a shared network. One `docker compose up` gets the full stack running.
Docker
Docker Compose
PostgreSQL 15
Redis 7
0.3
Database schema + Alembic migrations
Implement the full RDBMS schema from section 5.1: SOURCES, INDICATORS, INDICATOR_SOURCES, EVIDENCE, CONFIDENCE_SNAPSHOTS, USERS, ROLES, USER_ROLES, AUDIT_LOGS. All UUIDs as PKs. Write initial Alembic migration. Add composite UNIQUE(type, value) on indicators. Seed a default admin user.
SQLAlchemy 2
Alembic
PostgreSQL
0.4
Core models + Pydantic schemas
Build the class diagram domain model from section 6.1: Indicator, Evidence, Source, ConfidenceSnapshot Python classes. Add all enums: IndicatorType, IndicatorStatus, TrustTier, EvidenceType. These are the shared contracts for the entire codebase.
Pydantic v2
SQLAlchemy ORM
0.5
JWT auth + RBAC skeleton
FastAPI dependency for Bearer token validation. Three roles: ADMIN, ANALYST, API_CONSUMER. Protect all future routes with role guards from day one. Login endpoint returns JWT. Audit middleware that logs every authenticated request to AUDIT_LOGS.
python-jose
passlib
FastAPI Depends
✓
Gate: `docker compose up` runs the full stack. All tables exist. Admin can log in. CI is green.
Source management
1.1
Source CRUD API
POST/GET/PATCH/DELETE /api/v1/sources. Validates source category (community, research, commercial, internal), trust tier (Low/Medium/High), default_weight. Only ADMIN role can create/delete sources. This is the prerequisite for all ingestion.
FastAPI Router
ADMIN role
Ingestion service
1.2
Validator & Normalizer
Implement the Validator & Normalizer from the sequence diagram (4.1). Regex-per-type validation: IPv4, IPv6 (expand), domain (lowercase), URL (strip schema variants), MD5/SHA1/SHA256 (length + hex check). Returns ValidationResult with valid[], invalid[{field, reason}]. Partial ingestion: process valid rows, report errors. This is a pure function — easy to unit test exhaustively.
pytest
100% unit test coverage
1.3
POST /api/v1/indicators — manual ingestion
Accept CSV, TXT, JSON payloads. Run through Validator. For each NormalizedIndicator: SELECT existing by (type, value). If duplicate → UPDATE last_seen, INSERT indicator_sources ON CONFLICT. If new → INSERT indicator, INSERT indicator_sources. PUBLISH indicator.created to Redis. Return 202 Accepted with {ingested: N, duplicates: M, errors: K, error_details}. Mirror of the sequence diagram exactly.
Redis PUBLISH
ON CONFLICT
FastAPI
1.4
Scheduled HTTP feed puller
Celery Beat task: for each active source with a pull_url, fetch CSV/JSON on schedule, pipe through the same ingestion endpoint logic. Configurable interval per source. Graceful handling of HTTP errors, timeouts, malformed data — all logged, never crash the worker.
Celery Beat
httpx
retry/backoff
1.5
Ingestion integration tests
Test happy path, duplicate merge, partial batch with mixed valid/invalid, source not found, malformed CSV. Use pytest + httpx AsyncClient against a test DB. Verify Redis events are published. This test suite is your regression safety net for everything built on top.
pytest-asyncio
httpx
fakeredis
✓
Gate: POST a CSV of 100 mixed indicators. Check DB has correct records, duplicates merged, Redis events published, errors reported cleanly.
Enrichment engine
2.1
BaseEnricher + EnrichmentEngineFactory
Implement the class diagram from section 6.2. BaseEnricher has enrich(), getSupportedTypes(), getSourceName(). Factory maps IndicatorType → List[Enricher]. EnrichmentResult value object: indicator_id, source_name, evidence_type, raw_payload, confidence_delta, timestamp, success bool, error_message. EvidenceBuilder persists results as append-only EVIDENCE rows (no updated_at).
Strategy pattern
Factory pattern
append-only
2.2
WHOISEnricher + PassiveDNSEnricher
WHOIS: registrar, creation_date, update_date, registrant. 10s timeout, 3 retries with exponential backoff (2x, 4x, 8x) per the sequence diagram. Log failure, skip evidence, continue other enrichers. Passive DNS: resolve history, first_seen/last_seen per resolution. Domain age calculation. Test with mocked HTTP responses — never call real APIs in tests.
python-whois
dnspython
backoff
2.3
ASNEnricher + SSLEnricher + BehavioralAnalyser
ASN: AS number, country, hosting provider. SSL (domains/URLs only): fingerprint, issuer, subject, alt_names, valid_until. BehavioralAnalyser: detect short-lived domains (age < 30 days flag), detect infrastructure reuse (check existing ASN/IP in evidence), URL path pattern analysis. All return EnrichmentResult.
SSL cert APIs
behavioral flags
2.4
EnrichmentWorker (Celery) — async fan-out
CONSUME indicator.created from Redis. Determine applicable enrichers by indicator type. Dispatch as a parallel Celery group (chord). Each enricher task is independent — one failure doesn't block others. After all tasks complete, PUBLISH evidence.created for each successful result. This is the fan-out pattern from sequence diagram 4.2.
Celery group/chord
parallel tasks
Redis events
Correlation engine
2.5
Correlation Engine (3 checks)
CONSUME evidence.created. Run 3 sequential checks from sequence diagram 4.3: (1) Infrastructure Reuse — SELECT indicators sharing same ASN, INSERT CORRELATION_INFRA evidence, confidence_delta +5, reversible=true. (2) SSL Certificate Reuse — match cert fingerprint, +8 delta. (3) Multi-Source Sighting — count DISTINCT source_ids, INSERT MULTI_SOURCE_SIGHTING, delta = source_count × 3. PUBLISH correlation.created after all checks.
reversible evidence
correlation deltas
Confidence scoring engine
2.6
Confidence Scoring & Decay Engine
CONSUME evidence.created OR correlation.created. Weighted score: for each evidence, weight = source trust map (LOW=0.3, MEDIUM=0.6, HIGH=1.0), base_score += evidence.confidence_delta × weight. Enrichment depth bonus = count(distinct evidence_type) × 2. Correlation bonus = sum(correlation deltas). Analyst adj = sum(ANALYST_ADJUSTMENT deltas). Exponential decay: decay_factor = e^(-λ × days_elapsed) where λ=0.05. final_score = CLAMP(weighted_sum × decay_factor, 0, 100). INSERT confidence_snapshots (immutable). UPDATE indicators.current_confidence. Auto-expire if TTL elapsed AND score < 10. PUBLISH score.updated if delta > 5.
deterministic scoring
exponential decay
immutable snapshots
2.7
RationaleBuilder — explainability
Every confidence snapshot must include a structured JSON rationale: {score, factors: [{type, delta, evidence_id, source_name}], decay_factor, days_elapsed, calculated_at}. This is what the analyst UI will display. Test that an analyst can reconstruct exactly why a score is X from the rationale alone — no black boxes.
explainability
JSON rationale
2.8
Decay scheduler (Celery Beat)
Daily job: for all active indicators not scored in last 24h, re-run scoring engine with current timestamp. Indicators with TTL elapsed AND score < 10 get status=EXPIRED. Expired indicators remain queryable. Reappearance (new ingestion of expired indicator) re-triggers full enrichment pipeline.
Celery Beat
scheduled decay
2.9
Intelligence engine integration tests
End-to-end test: ingest IP → verify enrichment tasks fire → check evidence rows → verify correlation checks run → confirm confidence snapshot created with correct rationale → wait for decay to run → verify score decreases. Mock all external APIs. Test reversibility: withdraw evidence, verify score recalculates correctly.
e2e test
reversibility test
✓
Gate (MVP acceptance criteria 1-2): Confidence scores change meaningfully over time. Indicators expire automatically. Rationale is human-readable.
Query API (backend)
3.1
Indicator query API
GET /api/v1/indicators?type=&confidence_min=&status=&source=&page=&limit=. Returns paginated indicator list with current_confidence. GET /api/v1/indicators/{id} — full detail: indicator + evidence[] + confidence_snapshots[] (for timeline). GET /api/v1/indicators/{id}/correlations. All responses include the rationale JSON from the latest snapshot.
pagination
filtering
compound queries
3.2
Analyst action API endpoints
POST /api/v1/indicators/{id}/notes — analyst note (inserts ANALYST_NOTE evidence, confidence_delta=0, triggers re-score). PATCH /api/v1/indicators/{id}/confidence — manual promote/demote (ANALYST role only, INSERT ANALYST_ADJUSTMENT evidence, triggers re-score). PATCH /api/v1/indicators/{id}/revoke — sets status=REVOKED, INSERT REVOCATION evidence (confidence_delta=-50). PATCH /api/v1/indicators/{id}/ttl — adjust TTL within policy limits. All actions logged to AUDIT_LOGS.
ANALYST role
audit trail
re-scoring trigger
Frontend
3.3
React app scaffold + auth
Vite + React 18 + TypeScript. TanStack Query for server state. React Router for navigation. Login page → JWT stored in memory (not localStorage). Axios interceptor adds Bearer token. Route guard redirects unauthenticated users. Tailwind CSS for styling.
Vite
TanStack Query
React Router
Tailwind
3.4
Indicator list view
Searchable, filterable table: type badge, value, confidence score (color-coded 0-100), status, last seen. Filter bar: type, confidence range slider, status, source. Click row → indicator detail. Sort by confidence DESC by default. Pagination. Show stale/expired indicators in muted style.
React
confidence color-coding
3.5
Indicator detail page
Four panels from section 5.6.1: (1) Indicator metadata + current confidence score with rationale breakdown. (2) Evidence accordion — each enrichment result, source, timestamp, confidence contribution. (3) Confidence timeline — Recharts line chart of score over time with annotations for analyst actions. (4) Correlation panel — linked indicators with relationship type. All panels load in parallel via TanStack Query.
Recharts
TanStack Query
rationale display
3.6
Analyst action controls
Add note textarea + submit. Confidence adjustment: direction toggle (promote/demote) + delta slider + reason field. Revoke button with confirmation modal + mandatory reason. Adjust TTL date picker. All actions optimistically update UI, show toast on success/error, invalidate TanStack Query cache to refresh data.
optimistic updates
form validation
✓
Gate (MVP acceptance criteria 3-5): Analyst can explain why an indicator is high/low risk from the UI. Raw feeds are clearly more actionable post-enrichment. No blocking without human approval.
Export & API
4.1
Export API with confidence threshold gating
GET /api/v1/export?format=csv|json&confidence_min=&type=&status=. confidence_min < 70: returns directly. confidence_min ≥ 70 (high-confidence): requires explicit approval flag — analyst must set approved=true on the request. Enforces distribution controls from section 5.7.3. Log every export event to AUDIT_LOGS.
threshold gating
explicit approval
CSV/JSON
4.2
API Consumer endpoints
API Consumer role gets read-only access: query indicators, retrieve enrichment evidence. POST /api/v1/indicators still works for API submission. Rate limiting via FastAPI middleware (slowapi). API key management — ADMIN can issue/revoke API keys. All API Consumer access logged.
slowapi
API keys
API_CONSUMER role
Security & compliance
4.3
Audit log viewer (Admin UI)
Admin-only page: full audit trail queryable by user, action, entity_type, date range. Every confidence change, enrichment, analyst action, export is here. Supports the "historical state reconstruction" requirement from section 7.
ADMIN role
auditability
4.4
Security hardening
HTTPS enforced (TLS termination in nginx). CORS locked to known frontend origin. SQL injection impossible via ORM parameterisation (verify no raw string queries exist). Input size limits on all upload endpoints. Tamper-evident evidence: hash chain on EVIDENCE rows — each row stores SHA256(previous_hash + payload). Rate limiting on auth endpoints.
TLS
CORS
hash chain
rate limits
4.5
Performance validation
Ingest 1M indicators, verify query times under 2s via DB indexes: (type, value) UNIQUE, (status, current_confidence DESC) for list queries, (indicator_id, timestamp DESC) on evidence. Run Locust load test: 100 concurrent analysts, all standard queries under 2s. Enrichment pipeline throughput: verify async workers keep up with 1000 indicators/minute ingestion rate.
Locust
PostgreSQL indexes
1M scale test
4.6
Delivery documentation
Required by section 9: operational runbook (how to deploy, scale workers, add enrichment sources), scoring & decay logic doc (the λ parameter, weight map, rationale format), security review summary (threat model, controls), API reference (auto-generated from FastAPI OpenAPI spec).
runbook
OpenAPI docs
security review
✓
Final gate (all 5 MVP acceptance criteria): Full system passes acceptance test suite. Security review signed off. Deployed MVP environment live.



# Test Auth Flow
docker exec -it tip-api pytest tests/test_phase0_auth.py -v

# Test Indicator Ingestion Flow
docker exec -it tip-api pytest tests/test_phase1_ingestion.py -v

# Test Sources CRUD Flow
docker exec -it tip-api pytest tests/test_phase1_sources.py -v

# Test Intelligence, Scoring & Correlation Engine
docker exec -it tip-api pytest tests/test_phase2_intelligence.py -v
