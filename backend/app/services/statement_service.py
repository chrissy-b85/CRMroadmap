"""Statement generation service for NDIS CRM."""

from __future__ import annotations

import logging
import os
from calendar import month_name
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from sqlalchemy import and_, extract, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.invoice import Invoice
from app.models.participant import Participant
from app.models.plan import Plan
from app.models.statement import StatementRecord
from app.models.support_category import SupportCategory

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
_ORG_CONTACT = os.getenv("ORG_CONTACT", "info@ndiscrm.com.au | (02) 9000 0000")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _render_html(context: dict) -> str:
    """Render the monthly statement HTML template with Jinja2."""
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader(str(_TEMPLATES_DIR)), autoescape=True)
    template = env.get_template("statements/monthly_statement.html")
    return template.render(**context)


def _html_to_pdf(html: str) -> bytes:
    """Convert an HTML string to PDF bytes using WeasyPrint."""
    from weasyprint import HTML  # type: ignore[import]

    return HTML(string=html).write_pdf()  # type: ignore[no-any-return]


async def _get_active_plan(db: AsyncSession, participant_id: UUID) -> Plan | None:
    """Return the participant's currently active plan, if any."""
    result = await db.execute(
        select(Plan)
        .options(selectinload(Plan.support_categories))
        .where(
            and_(
                Plan.participant_id == participant_id,
                Plan.is_active.is_(True),
            )
        )
        .order_by(Plan.plan_start_date.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------


async def generate_monthly_statement(
    db: AsyncSession,
    participant_id: UUID,
    year: int,
    month: int,
) -> StatementRecord:
    """Generate a monthly PDF statement for a participant.

    Steps:
    1. Fetch all APPROVED invoices for the participant in the given month.
    2. Fetch participant details and current plan.
    3. Fetch budget summary per support category.
    4. Render HTML template using Jinja2.
    5. Convert HTML to PDF using WeasyPrint.
    6. Upload PDF to GCS (path: statements/{participant_id}/{year}-{month:02d}.pdf).
    7. Create/update StatementRecord in DB.
    8. Return the StatementRecord.
    """
    # 1. Fetch APPROVED invoices
    inv_result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.line_items), selectinload(Invoice.provider))
        .where(
            and_(
                Invoice.participant_id == participant_id,
                Invoice.status == "APPROVED",
                extract("year", Invoice.invoice_date) == year,
                extract("month", Invoice.invoice_date) == month,
            )
        )
        .order_by(Invoice.invoice_date)
    )
    invoices = inv_result.scalars().all()

    # 2. Fetch participant
    part_result = await db.execute(
        select(Participant).where(Participant.id == participant_id)
    )
    participant = part_result.scalar_one_or_none()
    if participant is None:
        raise ValueError(f"Participant {participant_id} not found")

    # 3. Fetch active plan and categories
    plan = await _get_active_plan(db, participant_id)
    categories = plan.support_categories if plan else []

    # Aggregate totals
    total_amount = sum((inv.total_amount for inv in invoices), Decimal("0.00"))
    total_gst = sum((inv.gst_amount for inv in invoices), Decimal("0.00"))
    invoice_count = len(invoices)

    # Build invoice dicts for template
    invoice_data = []
    for inv in invoices:
        provider_name = inv.provider.name if inv.provider else None  # type: ignore[union-attr]
        support_category = None
        if inv.line_items:
            first_item = inv.line_items[0]
            if first_item.support_category_id:
                cat_result = await db.execute(
                    select(SupportCategory).where(
                        SupportCategory.id == first_item.support_category_id
                    )
                )
                cat = cat_result.scalar_one_or_none()
                support_category = cat.ndis_support_category if cat else None

        invoice_data.append(
            {
                "id": str(inv.id),
                "invoice_date": str(inv.invoice_date) if inv.invoice_date else "—",
                "invoice_number": inv.invoice_number,
                "provider_name": provider_name,
                "support_category": support_category,
                "total_amount": inv.total_amount,
                "gst_amount": inv.gst_amount,
                "status": inv.status,
                "line_items": [
                    {"description": item.description} for item in inv.line_items
                ],
            }
        )

    # 4. Render HTML
    generated_date = datetime.now(tz=timezone.utc).strftime("%d %B %Y")
    statement_period = f"{month_name[month]} {year}"
    context = {
        "participant": participant,
        "plan": plan,
        "categories": categories,
        "invoices": invoice_data,
        "invoice_count": invoice_count,
        "total_amount": total_amount,
        "total_gst": total_gst,
        "statement_period": statement_period,
        "year": year,
        "month": month,
        "generated_date": generated_date,
        "org_contact": _ORG_CONTACT,
    }
    html = _render_html(context)

    # 5. Convert to PDF
    pdf_bytes = _html_to_pdf(html)

    # 6. Upload to GCS
    from app.integrations.gcs.client import GCSClient

    gcs = GCSClient()
    blob_path = f"statements/{participant_id}/{year}-{month:02d}.pdf"
    gcs_path = await gcs.upload_bytes(pdf_bytes, blob_path, "application/pdf")

    # 7. Create/update StatementRecord
    existing_result = await db.execute(
        select(StatementRecord).where(
            and_(
                StatementRecord.participant_id == participant_id,
                StatementRecord.year == year,
                StatementRecord.month == month,
            )
        )
    )
    record = existing_result.scalar_one_or_none()
    now = datetime.now(tz=timezone.utc)

    if record is None:
        record = StatementRecord(
            participant_id=participant_id,
            year=year,
            month=month,
            gcs_pdf_path=gcs_path,
            invoice_count=invoice_count,
            total_amount=total_amount,
            generated_at=now,
        )
        db.add(record)
    else:
        record.gcs_pdf_path = gcs_path
        record.invoice_count = invoice_count
        record.total_amount = total_amount
        record.generated_at = now

    await db.commit()
    await db.refresh(record)
    return record


async def generate_all_monthly_statements(
    db: AsyncSession,
    year: int,
    month: int,
) -> dict:
    """Generate statements for ALL active participants for a given month.

    Called by the Celery monthly batch job.

    Returns:
        dict with keys: generated, skipped (no invoices), failed.
    """
    result = await db.execute(
        select(Participant).where(Participant.is_active.is_(True))
    )
    participants = result.scalars().all()

    generated = 0
    skipped = 0
    failed = 0

    for participant in participants:
        # Check if there are any APPROVED invoices for this period
        count_result = await db.execute(
            select(Invoice).where(
                and_(
                    Invoice.participant_id == participant.id,
                    Invoice.status == "APPROVED",
                    extract("year", Invoice.invoice_date) == year,
                    extract("month", Invoice.invoice_date) == month,
                )
            )
        )
        if not count_result.scalars().first():
            skipped += 1
            continue

        try:
            await generate_monthly_statement(db, participant.id, year, month)
            generated += 1
        except Exception:  # noqa: BLE001
            logger.warning(
                "Failed to generate statement for participant %s (%d-%02d)",
                participant.id,
                year,
                month,
                exc_info=True,
            )
            failed += 1

    return {"generated": generated, "skipped": skipped, "failed": failed}


async def get_statement(
    db: AsyncSession,
    participant_id: UUID,
    year: int,
    month: int,
) -> StatementRecord | None:
    """Retrieve an existing statement record."""
    result = await db.execute(
        select(StatementRecord).where(
            and_(
                StatementRecord.participant_id == participant_id,
                StatementRecord.year == year,
                StatementRecord.month == month,
            )
        )
    )
    return result.scalar_one_or_none()


async def list_statements(
    db: AsyncSession,
    participant_id: UUID,
) -> list[StatementRecord]:
    """List all statement records for a participant, most recent first."""
    result = await db.execute(
        select(StatementRecord)
        .where(StatementRecord.participant_id == participant_id)
        .order_by(StatementRecord.year.desc(), StatementRecord.month.desc())
    )
    return list(result.scalars().all())


async def email_statement(
    db: AsyncSession,
    participant_id: UUID,
    year: int,
    month: int,
) -> StatementRecord:
    """Email a statement PDF to the participant via Graph API.

    Regenerates the PDF and sends it as an attachment.
    Updates the StatementRecord with emailed_at and email_message_id.
    """
    # Ensure a record exists (generate/update it)
    record = await get_statement(db, participant_id, year, month)
    if record is None:
        raise ValueError(
            f"No statement found for participant {participant_id} {year}-{month:02d}"
        )

    # Fetch participant email
    part_result = await db.execute(
        select(Participant).where(Participant.id == participant_id)
    )
    participant = part_result.scalar_one_or_none()
    if participant is None or not participant.email:
        raise ValueError(
            f"Participant {participant_id} has no email address configured"
        )

    # Regenerate the PDF with full invoice data for the attachment
    record = await generate_monthly_statement(db, participant_id, year, month)

    # Build PDF bytes with full context (reuse generate logic)
    inv_result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.line_items), selectinload(Invoice.provider))
        .where(
            and_(
                Invoice.participant_id == participant_id,
                Invoice.status == "APPROVED",
                extract("year", Invoice.invoice_date) == year,
                extract("month", Invoice.invoice_date) == month,
            )
        )
        .order_by(Invoice.invoice_date)
    )
    invoices = inv_result.scalars().all()
    plan = await _get_active_plan(db, participant_id)
    categories = plan.support_categories if plan else []
    total_amount = sum((inv.total_amount for inv in invoices), Decimal("0.00"))
    total_gst = sum((inv.gst_amount for inv in invoices), Decimal("0.00"))

    invoice_data = []
    for inv in invoices:
        provider_name = inv.provider.name if inv.provider else None  # type: ignore[union-attr]
        invoice_data.append(
            {
                "id": str(inv.id),
                "invoice_date": str(inv.invoice_date) if inv.invoice_date else "—",
                "invoice_number": inv.invoice_number,
                "provider_name": provider_name,
                "support_category": None,
                "total_amount": inv.total_amount,
                "gst_amount": inv.gst_amount,
                "status": inv.status,
                "line_items": [
                    {"description": item.description} for item in inv.line_items
                ],
            }
        )

    statement_period = f"{month_name[month]} {year}"
    context = {
        "participant": participant,
        "plan": plan,
        "categories": categories,
        "invoices": invoice_data,
        "invoice_count": len(invoices),
        "total_amount": total_amount,
        "total_gst": total_gst,
        "statement_period": statement_period,
        "year": year,
        "month": month,
        "generated_date": datetime.now(tz=timezone.utc).strftime("%d %B %Y"),
        "org_contact": _ORG_CONTACT,
    }
    html = _render_html(context)
    pdf_bytes = _html_to_pdf(html)

    # Send via Graph API
    from app.integrations.graph.client import GraphClient

    graph = GraphClient()
    subject = f"Your NDIS Statement for {statement_period}"
    body_html = (
        f"<p>Dear {participant.first_name},</p>"
        "<p>Please find attached your NDIS monthly statement for "
        f"<strong>{statement_period}</strong>.</p>"
        "<p>If you have any questions, please don't hesitate to contact us.</p>"
        "<p>Kind regards,<br>NDIS CRM Team</p>"
    )
    filename = f"NDIS_Statement_{year}-{month:02d}_{participant.ndis_number}.pdf"

    msg_id = await graph.send_mail(
        to_email=participant.email,
        subject=subject,
        body_html=body_html,
        attachment_bytes=pdf_bytes,
        attachment_name=filename,
    )

    # Update record
    now = datetime.now(tz=timezone.utc)
    record.emailed_at = now
    record.email_message_id = msg_id
    await db.commit()
    await db.refresh(record)
    return record
