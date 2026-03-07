"""Invoice ingestion pipeline service.

Polls the Outlook shared inbox via the Microsoft Graph API, runs OCR via
Google Document AI, and persists Invoice records to the database.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.document_ai.parser import InvoiceParseResult
from app.integrations.ocr import get_ocr_client
from app.integrations.gcs.client import GCSClient
from app.integrations.graph.client import GraphClient
from app.integrations.graph.config import GRAPH_PROCESSED_FOLDER_ID
from app.models.audit_log import AuditLog
from app.models.email_thread import EmailThread
from app.models.invoice import Invoice
from app.models.invoice_line_item import InvoiceLineItem
from app.models.provider import Provider

logger = logging.getLogger(__name__)


async def process_inbox(db: AsyncSession) -> dict:
    """Poll Outlook inbox, process new invoice emails, return summary.

    Called by Celery beat task or webhook.
    """
    graph = GraphClient()
    inbox_folder = "inbox"
    messages = await graph.get_inbox_messages(folder_id=inbox_folder)

    processed = 0
    failed = 0
    for message in messages:
        try:
            await process_invoice_email(db, message)
            processed += 1
        except Exception:  # noqa: BLE001
            logger.exception("Failed to process message %s", message.get("id"))
            failed += 1

    return {"processed": processed, "failed": failed, "total": len(messages)}


async def process_invoice_email(db: AsyncSession, message: dict) -> Invoice:
    """Process a single email message end-to-end.

    Steps:
    1. Find PDF attachments
    2. Upload PDF to GCS
    3. Run Document AI OCR
    4. Upload JSON result to GCS
    5. Match provider by ABN (or create unmatched record)
    6. Create Invoice + InvoiceLineItem records in DB
    7. Create EmailThread record
    8. Write audit log entry
    9. Mark email as read and move to processed folder
    """
    graph = GraphClient()
    gcs = GCSClient()
    doc_ai = get_ocr_client()

    message_id: str = message["id"]
    subject: str = message.get("subject", "")
    sender: str = (message.get("from", {}) or {}).get("emailAddress", {}).get(
        "address", ""
    )
    received_str: str = message.get("receivedDateTime", "")
    received_at: datetime | None = None
    if received_str:
        try:
            received_at = datetime.fromisoformat(received_str.replace("Z", "+00:00"))
        except ValueError:
            received_at = datetime.now(tz=timezone.utc)

    # 1. Find PDF attachments
    attachments = message.get("attachments") or await graph.get_message_attachments(
        message_id
    )
    pdf_attachments = [
        a
        for a in attachments
        if (a.get("contentType", "") == "application/pdf")
        or (a.get("name", "").lower().endswith(".pdf"))
    ]

    if not pdf_attachments:
        # No PDF – mark as read and move on without creating an invoice
        await graph.mark_message_as_read(message_id)
        if GRAPH_PROCESSED_FOLDER_ID:
            await graph.move_message_to_folder(message_id, GRAPH_PROCESSED_FOLDER_ID)
        raise ValueError(f"No PDF attachments found in message {message_id}")

    attachment = pdf_attachments[0]
    attachment_id: str = attachment["id"]
    filename: str = attachment.get("name", f"{message_id}.pdf")

    # 2. Download and upload PDF to GCS
    pdf_bytes: bytes = await graph.download_attachment(message_id, attachment_id)
    gcs_pdf_path = await gcs.upload_pdf(
        pdf_bytes, filename=filename, participant_id=None
    )

    # 3. Run Document AI OCR
    parse_result: InvoiceParseResult = await doc_ai.parse_invoice(pdf_bytes)

    # 4. Upload JSON result to GCS
    json_filename = filename.replace(".pdf", "_ocr.json")
    gcs_json_path = await gcs.upload_json(parse_result.raw_response, json_filename)

    # 5. Match provider by ABN
    provider: Provider | None = None
    if parse_result.supplier_abn:
        provider = await match_provider_by_abn(db, parse_result.supplier_abn)

    # 6. Create Invoice + InvoiceLineItem records
    invoice = Invoice(
        participant_id=None,
        provider_id=provider.id if provider else None,
        plan_id=None,
        invoice_number=parse_result.invoice_number,
        invoice_date=parse_result.invoice_date,
        due_date=parse_result.due_date,
        total_amount=parse_result.total_amount or Decimal("0.00"),
        gst_amount=parse_result.gst_amount or Decimal("0.00"),
        status="pending",
        ocr_confidence=parse_result.confidence_score,
        gcs_pdf_path=gcs_pdf_path,
        gcs_json_path=gcs_json_path,
    )
    db.add(invoice)
    await db.flush()  # Populate invoice.id before adding line items

    for item in parse_result.line_items:
        line = InvoiceLineItem(
            invoice_id=invoice.id,
            description=item.description,
            quantity=item.quantity or Decimal("1"),
            unit_price=item.unit_price or Decimal("0.00"),
            total=item.total or Decimal("0.00"),
            support_item_number=item.support_item_number,
        )
        db.add(line)

    # 7. Create EmailThread record
    thread = EmailThread(
        graph_thread_id=message.get("conversationId") or message_id,
        graph_message_id=message_id,
        subject=subject,
        sender_email=sender,
        sender_name=(message.get("from", {}) or {}).get("emailAddress", {}).get("name"),
        received_at=received_at,
        direction="inbound",
        has_attachments=bool(pdf_attachments),
        provider_id=provider.id if provider else None,
    )
    db.add(thread)
    await db.flush()

    invoice.email_thread_id = thread.id

    # 8. Write audit log entry
    audit = AuditLog(
        action="invoice_ingested",
        entity_type="Invoice",
        entity_id=invoice.id,
        new_values={
            "gcs_pdf_path": gcs_pdf_path,
            "supplier_name": parse_result.supplier_name,
            "invoice_number": parse_result.invoice_number,
        },
    )
    db.add(audit)

    await db.commit()
    await db.refresh(invoice)

    # 9. Mark email as read and move to processed folder
    try:
        await graph.mark_message_as_read(message_id)
        if GRAPH_PROCESSED_FOLDER_ID:
            await graph.move_message_to_folder(message_id, GRAPH_PROCESSED_FOLDER_ID)
    except Exception:  # noqa: BLE001
        logger.warning(
            "Could not mark/move message %s after processing", message_id, exc_info=True
        )

    return invoice


async def match_provider_by_abn(db: AsyncSession, abn: str) -> Provider | None:
    """Look up a provider by ABN from the parsed invoice."""
    normalized = abn.replace(" ", "")
    result = await db.execute(
        select(Provider).where(Provider.abn == normalized)
    )
    return result.scalar_one_or_none()
