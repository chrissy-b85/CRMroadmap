"""Celery beat schedule — poll invoice inbox every 5 minutes."""
from celery.schedules import crontab

from app.worker.celery_app import celery_app

celery_app.conf.beat_schedule = {
    "poll-invoice-inbox-every-5-minutes": {
        "task": "app.worker.tasks.poll_invoice_inbox",
        "schedule": crontab(minute="*/5"),
    },
}
