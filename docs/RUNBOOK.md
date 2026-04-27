# TIP Operational Runbook (D-Drive Deployment)

This document specifies the operational instructions required to deploy, scale, and expand the Threat Intelligence Platform (TIP) optimally locally.

## 1. Deployment Initialization

### Using Docker Compose
The platform is designed to instantly deploy securely utilizing the default `docker-compose.yml`.

1. **Bootstrap the Network**:
```bash
docker compose up -d --build
```
This provisions:
- `tip-postgres`: Deep data lake and schema states.
- `tip-redis`: Queue bindings and in-memory caches.
- `tip-api`: The FastAPI layer terminating endpoints.
- `tip-worker` & `tip-beat`: The Celery backend evaluating enrichment plugins concurrently.
- `tip-frontend`: Vite configuration mapping the web page natively over React setups!
- `tip-nginx`: The secure TLS terminator bouncing external hits optimally to the private subnet natively mapping your `D:` workspace directories.

2. **Migrate the Database**:
Execute database structures prior to the first ingestion wave:
```bash
docker exec -it tip-api alembic upgrade head
```

## 2. Scaling the Enrichment Workers

To double operational bounds dynamically securely:
```bash
docker compose up -d --scale tip-worker=3
```
This distributes load strictly over 3 independent decoupled Python celery containers mapped dynamically leveraging `Redis` task locks.

## 3. Adding New Enrichment Sources

To expand ingestion coverage natively extending towards URL scanning APIs effectively:
1. **Instantiate Target Source**: Connect to PostgreSQL locally and deploy a new Source target explicitly mapping its Reliability factor (Ex: `90`).
```sql
INSERT INTO sources (name, type, reliability) 
VALUES ('Generic Reputation Mapper', 'WEB_API', 95.0);
```
2. **Assign Plugin Code**: 
Develop the execution schema securely inside `backend/app/services/enrichment/`.
```python
@celery_app.task
def fetch_safe_browsing(indicator_id: str):
    pass
```
3. **Register Cron Execution**:
Map the binding towards `tip-beat` scheduled intervals tracking `backend/app/workers/celery_app.py`.
