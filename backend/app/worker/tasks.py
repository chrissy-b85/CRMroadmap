"""Celery tasks for invoice inbox polling and validation."""

import asyncio
import logging

from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.worker.tasks.poll_invoice_inbox", bind=True, max_retries=3)
def poll_invoice_inbox(self):  # type: ignore[no-untyped-def]
    """Scheduled task: poll Outlook inbox every 5 minutes."""
    from app.db import AsyncSessionLocal
    from app.services.invoice_ingestion_service import process_inbox

    async def _run():
        async with AsyncSessionLocal() as db:
            return await process_inbox(db)

    try:
        return asyncio.run(_run())
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "poll_invoice_inbox failed (attempt %s): %s",
            self.request.retries + 1,
            exc,
        )
        raise self.retry(exc=exc, countdown=60) from exc


@celery_app.task(
    name="app.worker.tasks.process_single_invoice", bind=True, max_retries=3
)
def process_single_invoice(self, message_id: str):  # type: ignore[no-untyped-def]
    """Process a single invoice email by message ID."""
    from app.db import AsyncSessionLocal
    from app.integrations.graph.client import GraphClient
    from app.services.invoice_ingestion_service import process_invoice_email

    async def _run():
        graph = GraphClient()
        attachments = await graph.get_message_attachments(message_id)
        message = {"id": message_id, "attachments": attachments}
        async with AsyncSessionLocal() as db:
            invoice = await process_invoice_email(db, message)
            return str(invoice.id)

    try:
        invoice_id = asyncio.run(_run())
        # Automatically trigger validation after successful ingestion
        validate_invoice_task.delay(invoice_id)
        return invoice_id
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "process_single_invoice failed for %s (attempt %s): %s",
            message_id,
            self.request.retries + 1,
            exc,
        )
        raise self.retry(exc=exc, countdown=60) from exc


@celery_app.task(name="app.worker.tasks.check_all_budget_alerts")
def check_all_budget_alerts() -> dict:  # type: ignore[return]
    """Daily task: check all active plans for budget alerts."""
    from app.db import AsyncSessionLocal
    from app.services.budget_tracking_service import get_all_active_plan_alerts

    async def _run():
        async with AsyncSessionLocal() as db:
            alerts = await get_all_active_plan_alerts(db)
            return {"alert_count": len(alerts)}

    try:
        return asyncio.run(_run())
    except Exception as exc:  # noqa: BLE001
        logger.warning("check_all_budget_alerts failed: %s", exc)
        raise


@celery_app.task(
    name="app.worker.tasks.validate_invoice_task", bind=True, max_retries=3
)
def validate_invoice_task(self, invoice_id: str):  # type: ignore[no-untyped-def]
    """Run validation on a newly ingested invoice."""
    from uuid import UUID

    from app.db import AsyncSessionLocal
    from app.services.invoice_validation_service import validate_invoice

    async def _run():
        async with AsyncSessionLocal() as db:
            report = await validate_invoice(db, UUID(invoice_id))
            return {"invoice_id": invoice_id, "final_status": report.final_status}

    try:
        return asyncio.run(_run())
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "validate_invoice_task failed for %s (attempt %s): %s",
            invoice_id,
            self.request.retries + 1,
            exc,
        )
        raise self.retry(exc=exc, countdown=30) from exc


@celery_app.task(name="app.worker.tasks.poll_correspondence_inbox")
def poll_correspondence_inbox() -> dict:  # type: ignore[return]
    """Every 15 minutes: check mailbox for new inbound correspondence."""
    from app.db import AsyncSessionLocal
    from app.services.correspondence_service import (
        poll_correspondence_inbox as _poll,
    )

    async def _run():
        async with AsyncSessionLocal() as db:
            return await _poll(db)

    try:
        return asyncio.run(_run())
    except Exception as exc:  # noqa: BLE001
        logger.warning("poll_correspondence_inbox failed: %s", exc)
        raise


@celery_app.task(name="app.worker.tasks.send_budget_alert_emails")
def send_budget_alert_emails() -> dict:  # type: ignore[return]
    """Daily: send low budget alert emails for CRITICAL/WARNING plans."""
    from app.db import AsyncSessionLocal
    from app.services.budget_tracking_service import get_all_active_plan_alerts

    async def _run():
        async with AsyncSessionLocal() as db:
            alerts = await get_all_active_plan_alerts(db)
            return {"alert_count": len(alerts)}

    try:
        return asyncio.run(_run())
    except Exception as exc:  # noqa: BLE001
        logger.warning("send_budget_alert_emails failed: %s", exc)
        raise


@celery_app.task(name="app.worker.tasks.send_plan_expiry_warnings")
def send_plan_expiry_warnings() -> dict:  # type: ignore[return]
    """Daily: send plan expiry warnings for plans expiring in ≤30 days."""
    from datetime import date, timedelta

    from app.db import AsyncSessionLocal
    from app.models.participant import Participant
    from app.models.plan import Plan
    from app.services.email_notification_service import EmailNotificationService

    async def _run():
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            cutoff = date.today() + timedelta(days=30)
            result = await db.execute(
                select(Plan).where(
                    Plan.is_active.is_(True),
                    Plan.plan_end_date <= cutoff,
                )
            )
            plans = result.scalars().all()
            svc = EmailNotificationService()
            sent = 0
            for plan in plans:
                part_result = await db.execute(
                    select(Participant).where(Participant.id == plan.participant_id)
                )
                participant = part_result.scalar_one_or_none()
                if participant and participant.email:
                    days_remaining = (plan.plan_end_date - date.today()).days
                    try:
                        await svc.send_plan_expiry_warning(
                            participant_email=participant.email,
                            participant_name=f"{participant.first_name} {participant.last_name}",
                            plan=plan,
                            days_remaining=days_remaining,
                        )
                        sent += 1
                    except Exception:  # noqa: BLE001
                        logger.warning(
                            "Failed to send expiry warning for plan %s", plan.id, exc_info=True
                        )
            return {"sent": sent, "total_expiring": len(plans)}

    try:
        return asyncio.run(_run())
    except Exception as exc:  # noqa: BLE001
        logger.warning("send_plan_expiry_warnings failed: %s", exc)
        raise
def reconcile_xero_payments(self):  # type: ignore[no-untyped-def]
    """Daily task: poll Xero for payment status updates on APPROVED invoices."""
    from app.db import AsyncSessionLocal
    from app.services.xero_sync_service import reconcile_xero_invoices

    async def _run():
        async with AsyncSessionLocal() as db:
            return await reconcile_xero_invoices(db)

    try:
        return asyncio.run(_run())
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "reconcile_xero_payments failed (attempt %s): %s",
            self.request.retries + 1,
            exc,
        )
        raise self.retry(exc=exc, countdown=300) from exc


@celery_app.task(name="app.worker.tasks.generate_monthly_statements")
def generate_monthly_statements() -> dict:  # type: ignore[return]
    """Run on 1st of each month at 02:00 AEST.

    Generate statements for all active participants for the previous month,
    then email each statement via Outlook (Graph API).
    """
    from datetime import date

    from app.db import AsyncSessionLocal
    from app.services.statement_service import generate_all_monthly_statements

    # Generate for the previous month
    today = date.today()
    if today.month == 1:
        year, month = today.year - 1, 12
    else:
        year, month = today.year, today.month - 1

    async def _run():
        async with AsyncSessionLocal() as db:
            return await generate_all_monthly_statements(db, year, month)

    try:
        result = asyncio.run(_run())
        logger.info(
            "generate_monthly_statements completed for %d-%02d: %s", year, month, result
        )
        return result
    except Exception as exc:  # noqa: BLE001
        logger.warning("generate_monthly_statements failed: %s", exc)
        raise
