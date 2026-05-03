#!/bin/bash
set -e

# Run migrations
alembic upgrade head

# Run database seed
python -m app.db.seed

# Start Celery worker in the background
python -m celery -A app.workers.celery_app worker --loglevel=info &

# Start the API server in the foreground
uvicorn app.main:app --host 0.0.0.0 --port $PORT
