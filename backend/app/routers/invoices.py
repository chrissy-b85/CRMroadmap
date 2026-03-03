"""FastAPI router for invoice management and ingestion endpoints."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user, require_role
from app.db import get_db
from app.models.audit_log import AuditLog
from app.models.invoice import Invoice
from app.models.participant import SupportCategory
from app.schemas.invoice import InvoiceListOut, InvoiceOut
from app.schemas.invoice_validation import ValidationReportOut, ValidationResultOut

router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.post("/ingest/trigger", status_code=status.HTTP_202_ACCEPTED)
async def trigger_inbox_poll(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("Admin")),
):
    """Manually trigger an inbox poll (Admin only). Returns a confirmation."""
    from app.services.invoice_ingestion_service import process_inbox

    background_tasks.add_task(process_inbox, db)
    return {"detail": "Inbox poll triggered", "status": "accepted"}


@router.get("/", response_model=InvoiceListOut)
async def list_invoices(
    page: int = 1,
    page_size: int = 20,
    invoice_status: str | None = None,
    participant_id: UUID | None = None,
    provider_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List invoices with optional filters for status, participant, and provider."""
    query = select(Invoice).options(selectinload(Invoice.line_items))
    count_query = select(func.count()).select_from(Invoice)

    if invoice_status:
        query = query.where(Invoice.status == invoice_status)
        count_query = count_query.where(Invoice.status == invoice_status)
    if participant_id:
        query = query.where(Invoice.participant_id == participant_id)
        count_query = count_query.where(Invoice.participant_id == participant_id)
    if provider_id:
        query = query.where(Invoice.provider_id == provider_id)
        count_query = count_query.where(Invoice.provider_id == provider_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    items = result.scalars().all()

    return InvoiceListOut(items=items, total=total, page=page, page_size=page_size)


@router.get("/{invoice_id}", response_model=InvoiceOut)
async def get_invoice(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a single invoice with its line items."""
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.line_items))
        .where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found"
        )
    return invoice


@router.post("/{invoice_id}/validate", response_model=ValidationReportOut)
async def trigger_validation(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("Coordinator")),
):
    """Manually trigger validation for an invoice (Admin/Coordinator)."""
    from app.services.invoice_validation_service import validate_invoice

    try:
        report = await validate_invoice(db, invoice_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    return ValidationReportOut(
        invoice_id=report.invoice_id,
        passed=report.passed,
        final_status=report.final_status,
        results=[
            ValidationResultOut(
                rule_name=r.rule_name,
                passed=r.passed,
                message=r.message,
                severity=r.severity,
            )
            for r in report.results
        ],
        validated_at=datetime.now(tz=timezone.utc),
    )


@router.post("/{invoice_id}/approve", response_model=InvoiceOut)
async def approve_invoice(
    invoice_id: UUID,
    notes: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("Coordinator")),
):
    """Approve a PENDING_APPROVAL invoice. Requires Coordinator role.

    - Sets status to APPROVED
    - Records reviewed_by, reviewed_at
    - Updates support category budget_spent
    - Writes audit log
    """
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.line_items))
        .where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found"
        )
    if invoice.status != "PENDING_APPROVAL":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Invoice status is '{invoice.status}', "
                "must be PENDING_APPROVAL to approve."
            ),
        )

    now = datetime.now(tz=timezone.utc)
    invoice.status = "APPROVED"
    invoice.reviewed_at = now

    # Update budget_spent for each support category
    for item in invoice.line_items:
        if item.support_category_id:
            cat_result = await db.execute(
                select(SupportCategory).where(
                    SupportCategory.id == item.support_category_id
                )
            )
            cat = cat_result.scalar_one_or_none()
            if cat is not None:
                from decimal import Decimal

                cat.budget_spent = (cat.budget_spent or Decimal("0")) + (
                    item.total or Decimal("0")
                )

    audit = AuditLog(
        action="invoice_approved",
        entity_type="Invoice",
        entity_id=invoice.id,
        new_values={
            "status": "APPROVED",
            "reviewed_at": now.isoformat(),
            "notes": notes,
        },
    )
    db.add(audit)
    await db.commit()

    # Reload with line_items to satisfy response model
    reload_result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.line_items))
        .where(Invoice.id == invoice_id)
    )
    invoice = reload_result.scalar_one()
    return invoice


@router.post("/{invoice_id}/reject", response_model=InvoiceOut)
async def reject_invoice(
    invoice_id: UUID,
    reason: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("Coordinator")),
):
    """Reject an invoice. Requires Coordinator role.

    - Sets status to REJECTED
    - Records reason
    - Writes audit log
    """
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found"
        )

    now = datetime.now(tz=timezone.utc)
    invoice.status = "REJECTED"
    invoice.reviewed_at = now
    invoice.rejection_reason = reason

    audit = AuditLog(
        action="invoice_rejected",
        entity_type="Invoice",
        entity_id=invoice.id,
        new_values={
            "status": "REJECTED",
            "reason": reason,
            "reviewed_at": now.isoformat(),
        },
    )
    db.add(audit)
    await db.commit()
    reload_result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.line_items))
        .where(Invoice.id == invoice_id)
    )
    return reload_result.scalar_one()


@router.post("/{invoice_id}/request-info", response_model=InvoiceOut)
async def request_info(
    invoice_id: UUID,
    message: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("Coordinator")),
):
    """Request more information from provider.

    - Sets status to INFO_REQUESTED
    - Writes audit log (Outlook notification handled in Sprint 9)
    """
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found"
        )

    invoice.status = "INFO_REQUESTED"

    audit = AuditLog(
        action="invoice_info_requested",
        entity_type="Invoice",
        entity_id=invoice.id,
        new_values={
            "status": "INFO_REQUESTED",
            "message": message,
        },
    )
    db.add(audit)
    await db.commit()
    reload_result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.line_items))
        .where(Invoice.id == invoice_id)
    )
    return reload_result.scalar_one()
