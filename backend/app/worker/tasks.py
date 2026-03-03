"""Celery tasks for invoice inbox polling."""
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
        logger.warning("poll_invoice_inbox failed (attempt %s): %s", self.request.retries + 1, exc)
        raise self.retry(exc=exc, countdown=60) from exc


@celery_app.task(name="app.worker.tasks.process_single_invoice", bind=True, max_retries=3)
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
        return asyncio.run(_run())
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "process_single_invoice failed for %s (attempt %s): %s",
            message_id,
            self.request.retries + 1,
            exc,
        )
        raise self.retry(exc=exc, countdown=60) from exc
