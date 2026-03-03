"""Celery beat schedule — poll invoice inbox every 5 minutes."""

from celery.schedules import crontab

from app.worker.celery_app import celery_app

celery_app.conf.beat_schedule = {
    "poll-invoice-inbox-every-5-minutes": {
        "task": "app.worker.tasks.poll_invoice_inbox",
        "schedule": crontab(minute="*/5"),
    },
    "check-all-budget-alerts-daily": {
        "task": "app.worker.tasks.check_all_budget_alerts",
        "schedule": crontab(hour="7", minute="0"),
    },
    "reconcile-xero-payments-daily": {
        "task": "app.worker.tasks.reconcile_xero_payments",
        "schedule": crontab(hour="2", minute="0"),
    },
    "generate-monthly-statements": {
        "task": "app.worker.tasks.generate_monthly_statements",
        "schedule": crontab(day_of_month=1, hour=2, minute=0),
    },
}
