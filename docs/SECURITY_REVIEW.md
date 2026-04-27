# Security Review & Threat Model

This summary provides structural insight evaluating OSINT deployment security structures validating boundaries logically protecting the backend.

## Threat 1: Unauthorized Data Manipulation
- **Description**: Explicit tampering dropping queries modifying internal states over endpoints locally.
- **Controls**:
  - Rigid OAuth2 JWT Bearer structures executing natively inside `deps.py`.
  - Roles (`ADMIN`, `ANALYST`, `API_CONSUMER`) define bounds explicitly dropping requests rendering `403 Forbidden` errors natively over endpoints.
  - Immutability arrays! The `Evidence.hash` natively computes `SHA256(previous_hash + payload)` locking history dynamically against direct unauthenticated root `DB` modification bounds!

## Threat 2: Application Subversion (SQLi)
- **Description**: Attackers parsing mapping scripts dynamically over the `value` fields logically attempting string executions dropping internal Postgres states.
- **Controls**:
  - Securely mounted `SQLAlchemy 2.0` models strictly parameterized resolving mapped bounds securely without requiring any explicitly dropped `.execute("INSERT raw")` definitions dynamically.

## Threat 3: Denial Of Service (DOS)
- **Description**: Exhausting local connections sending massive CSV files over standard TCP pipelines.
- **Controls**:
  - `nginx.conf` establishes limits forcing drops over uploads natively at `client_max_body_size 5M;`.
  - The API structure relies natively securely upon `slowapi` ensuring login routes drop connection endpoints safely at `5 requests / minute`.

## Threat 4: Data In-Transit Eavesdropping
- **Description**: Network sniffers tracking API tokens extracting explicitly internal structures locally.
- **Controls**:
  - HTTP `80` automatically proxies strictly resolving structural mapping to local TLS `443`.
  - Rigid CORS logic explicitly mapped safely reflecting domains dynamically natively via the `FRONTEND_CORS_ORIGINS`.
