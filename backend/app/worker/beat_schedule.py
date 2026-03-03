"""Celery beat schedule — poll invoice inbox every 5 minutes."""
from celery.schedules import crontab

from app.worker.celery_app import celery_app

celery_app.conf.beat_schedule = {
    "poll-invoice-inbox-every-5-minutes": {
        "task": "app.worker.tasks.poll_invoice_inbox",
        "schedule": crontab(minute="*/5"),
    },
<<<<<<< copilot/implement-budget-tracking-logic
    "check-all-budget-alerts-daily": {
        "task": "app.worker.tasks.check_all_budget_alerts",
        "schedule": crontab(hour="7", minute="0"),
=======
    "reconcile-xero-payments-daily": {
        "task": "app.worker.tasks.reconcile_xero_payments",
        "schedule": crontab(hour="2", minute="0"),
>>>>>>> main
    },
}
