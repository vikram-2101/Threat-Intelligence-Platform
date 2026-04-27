# OpenAPI 3.0 API Reference

The entire architecture maps APIs directly generating Swagger interfaces rendering documentation cleanly across the active infrastructure.

## Interactive API Docs

When running your specific stack:

- **Swagger UI**: Accessible cleanly via [https://localhost/docs](https://localhost/docs). Provides executable interfaces generating JWT and `X-API-Key` headers natively seamlessly dropping execution calls safely!
- **ReDoc UI**: Alternative cleaner UX parsing logic bounding structurally across [https://localhost/redoc](https://localhost/redoc).
- **JSON Schema**: Download raw configurations executing bounds natively via [https://localhost/openapi.json](https://localhost/openapi.json).

## Endpoint Core Structure

### 1. Indicators (`/api/v1/indicators`)
- `POST /`: Submit bulk payloads mapping arrays externally utilizing `JSON` natively or streaming via `multipart/form-data` natively.
- `GET /`: Retrieve paginated limit bounds matching filtering fields (`confidence_min=70`, `status=ACTIVE`).
- `GET /{id}`: Read deep snapshots calculating confidence metrics seamlessly surfacing `EvidenceResponse` dynamically.
- `GET /{id}/correlations`: Drop structural `MULTI_SIGHTING` logic seamlessly returning bounded metrics executing specific logic structures locally.

### 2. Analyst Actions (`/api/v1/indicators/{id}/*`)
- `PATCH /confidence`: Modifies confidence structurally securely.
- `POST /notes`: Inserts analytical information executing safely over evidence pipelines.
- `PATCH /revoke`: Overrides standard states natively structurally triggering immediate expiry definitions.

### 3. API Keys (`/api/v1/auth/api-keys`)
- `POST /`: Safely sets explicitly structural bounds locking strings generating secure mints locally!
- `DELETE /{id}`: Tears down bindings securely.

### 4. Exports (`/api/v1/export`)
- `GET /`: Streams downloads returning structurally validated lists via `.json` or dynamically mapping limits pushing out `.csv` binaries locally!

### 5. Audit Log Bounds (`/api/v1/audit-logs`)
- `GET /`: Provides heavily paginated metrics parsing structural actions explicitly enforcing strict `RoleChecker([RoleName.ADMIN])`.
