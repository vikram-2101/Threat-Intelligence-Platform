FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /app

# Install system dependencies for Postgres and building packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject config first to leverage Docker cache
COPY pyproject.toml .

# Install dependencies (including dev groups for hot-reloading if needed)
RUN pip install --no-cache-dir .

# Create a non-root user to run the application
RUN groupadd -r celery && useradd -r -g celery -d /app -s /sbin/nologin celery

# Copy the rest of the code
COPY --chown=celery:celery . .

USER celery

# Default command for the API service
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]