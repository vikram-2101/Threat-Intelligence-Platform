from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "tip_workers",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.enrichment_worker",
        "app.workers.correlation_worker",
        "app.workers.scoring_worker",
        "app.workers.decay_scheduler",
        "app.workers.tasks",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
)

# Celery Beat Schedule
celery_app.conf.beat_schedule = {
    "daily-decay-job": {
        "task": "app.workers.decay_scheduler.run_daily_decay",
        "schedule": 86400.0,  # 24 hours
    },
    "fetch-external-feeds-job": {
        "task": "app.workers.tasks.fetch_external_feeds",
        "schedule": 300.0,  # Every 5 minutes
    },
}
