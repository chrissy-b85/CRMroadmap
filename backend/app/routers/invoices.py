"""FastAPI router for invoice management and ingestion endpoints."""
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user, require_role
from app.db import get_db
from app.models.invoice import Invoice
from app.schemas.invoice import InvoiceListOut, InvoiceOut

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
