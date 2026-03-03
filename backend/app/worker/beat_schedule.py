"""Celery beat schedule — scheduled tasks for the NDIS CRM."""
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
    "poll-correspondence-inbox-every-15-minutes": {
        "task": "app.worker.tasks.poll_correspondence_inbox",
        "schedule": crontab(minute="*/15"),
    },
    "send-budget-alert-emails-daily": {
        "task": "app.worker.tasks.send_budget_alert_emails",
        "schedule": crontab(hour="8", minute="0"),
    },
    "send-plan-expiry-warnings-daily": {
        "task": "app.worker.tasks.send_plan_expiry_warnings",
        "schedule": crontab(hour="8", minute="15"),
    },
}
