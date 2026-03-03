"""Xero two-way sync service.

Handles syncing CRM invoices to Xero as bills and updating CRM invoice
status when Xero marks a bill as paid.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.integrations.xero.client import XeroClient
from app.models.audit_log import AuditLog
from app.models.invoice import Invoice
from app.models.provider import Provider
from app.models.xero_connection import XeroConnection

logger = logging.getLogger(__name__)

# Mapping from NDIS support category names to Xero account codes.
# Extend as required for your chart of accounts.
ACCOUNT_CODE_MAP: dict[str, str] = {
    "Support Coordination": "400",
    "Daily Activities": "401",
    "Social Community": "402",
    "Capacity Building": "403",
    "Capital Supports": "404",
}
DEFAULT_ACCOUNT_CODE = "200"


async def _get_xero_client(db: AsyncSession) -> XeroClient:
    """Load the active XeroConnection and return an initialised client."""
    result = await db.execute(
        select(XeroConnection)
        .where(XeroConnection.is_active.is_(True))
        .order_by(XeroConnection.created_at.desc())
        .limit(1)
    )
    conn = result.scalar_one_or_none()
    if conn is None:
        raise ValueError("No active Xero connection found")

    # Refresh token if expired
    now = datetime.now(tz=timezone.utc)
    token_expiry = conn.token_expiry
    if token_expiry.tzinfo is None:
        token_expiry = token_expiry.replace(tzinfo=timezone.utc)

    client = XeroClient(
        access_token=conn.access_token,
        refresh_token=conn.refresh_token,
        tenant_id=conn.tenant_id,
    )

    if now >= token_expiry:
        tokens = await client.refresh_access_token(conn.refresh_token)
        conn.access_token = tokens.access_token
        conn.refresh_token = tokens.refresh_token
        from datetime import timedelta

        conn.token_expiry = now + timedelta(seconds=tokens.expires_in)
        await db.commit()
        client.access_token = tokens.access_token
        client.refresh_token = tokens.refresh_token

    return client


async def _get_or_create_xero_contact(
    db: AsyncSession,
    client: XeroClient,
    provider: Provider,
) -> str:
    """Return the Xero ContactID for *provider*, creating one if needed."""
    if provider.xero_contact_id:
        return provider.xero_contact_id

    # Search by ABN first
    contacts = await client.get_contacts(provider.abn)
    if contacts:
        contact_id = contacts[0].contact_id
    else:
        xero_contact = await client.create_contact(provider)
        contact_id = xero_contact.contact_id

    provider.xero_contact_id = contact_id
    await db.flush()
    return contact_id


async def sync_approved_invoice_to_xero(db: AsyncSession, invoice_id: UUID) -> str:
    """Push an approved CRM invoice to Xero as a Bill.

    Steps:
    1. Get/create Xero contact for provider (match by ABN)
    2. Create Xero Bill with line items mapped to Xero account codes
    3. Store xero_invoice_id on the CRM invoice record
    4. Write audit log

    Returns the Xero invoice ID.
    """
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.line_items))
        .where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if invoice is None:
        raise ValueError(f"Invoice {invoice_id} not found")

    if invoice.status != "APPROVED":
        raise ValueError(
            f"Invoice {invoice_id} is not APPROVED (status={invoice.status})"
        )

    client = await _get_xero_client(db)

    # Resolve provider and Xero contact
    contact_id: str
    if invoice.provider_id:
        prov_result = await db.execute(
            select(Provider).where(Provider.id == invoice.provider_id)
        )
        provider = prov_result.scalar_one_or_none()
        if provider:
            contact_id = await _get_or_create_xero_contact(db, client, provider)
        else:
            raise ValueError(
                f"Provider {invoice.provider_id} not found for invoice {invoice_id}"
            )
    else:
        raise ValueError(f"Invoice {invoice_id} has no provider")

    # Build line items
    line_items = []
    for item in invoice.line_items:
        # Try to resolve account code from support category name
        account_code = DEFAULT_ACCOUNT_CODE
        if item.support_category_id:
            from app.models.participant import SupportCategory

            cat_result = await db.execute(
                select(SupportCategory).where(
                    SupportCategory.id == item.support_category_id
                )
            )
            cat = cat_result.scalar_one_or_none()
            if cat and cat.ndis_support_category:
                account_code = ACCOUNT_CODE_MAP.get(
                    cat.ndis_support_category, DEFAULT_ACCOUNT_CODE
                )

        line_items.append(
            {
                "description": item.description or "",
                "quantity": float(item.quantity or 1),
                "unit_amount": float(item.unit_price or 0),
                "account_code": account_code,
            }
        )

    invoice_data = {
        "contact_id": contact_id,
        "invoice_number": invoice.invoice_number or "",
        "date": invoice.invoice_date.isoformat() if invoice.invoice_date else "",
        "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
        "line_items": line_items,
    }

    xero_bill = await client.create_bill(invoice_data)

    invoice.xero_invoice_id = xero_bill.xero_invoice_id

    audit = AuditLog(
        action="xero_bill_created",
        entity_type="Invoice",
        entity_id=invoice.id,
        new_values={
            "xero_invoice_id": xero_bill.xero_invoice_id,
            "xero_status": xero_bill.status,
        },
    )
    db.add(audit)
    await db.commit()

    logger.info(
        "Invoice %s synced to Xero as bill %s",
        invoice_id,
        xero_bill.xero_invoice_id,
    )
    return xero_bill.xero_invoice_id


async def sync_payment_from_xero(db: AsyncSession, xero_invoice_id: str) -> Invoice:
    """Update CRM invoice status to PAID when Xero marks the bill as paid.

    Steps:
    1. Find CRM invoice by xero_invoice_id
    2. Update status to PAID
    3. Record payment date
    4. Write audit log
    """
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.line_items))
        .where(Invoice.xero_invoice_id == xero_invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if invoice is None:
        raise ValueError(
            f"No CRM invoice found with xero_invoice_id={xero_invoice_id}"
        )

    now = datetime.now(tz=timezone.utc)
    invoice.status = "PAID"
    invoice.reviewed_at = now

    audit = AuditLog(
        action="xero_payment_received",
        entity_type="Invoice",
        entity_id=invoice.id,
        new_values={
            "status": "PAID",
            "xero_invoice_id": xero_invoice_id,
            "paid_at": now.isoformat(),
        },
    )
    db.add(audit)
    await db.commit()
    await db.refresh(invoice)

    logger.info("Invoice %s marked PAID via Xero webhook", invoice.id)
    return invoice


async def void_xero_bill(db: AsyncSession, invoice_id: UUID) -> None:
    """Void the Xero bill associated with an approved invoice that was reversed."""
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if invoice is None:
        raise ValueError(f"Invoice {invoice_id} not found")

    if not invoice.xero_invoice_id:
        logger.warning("Invoice %s has no xero_invoice_id; nothing to void", invoice_id)
        return

    client = await _get_xero_client(db)
    await client.void_bill(invoice.xero_invoice_id)

    audit = AuditLog(
        action="xero_bill_voided",
        entity_type="Invoice",
        entity_id=invoice.id,
        new_values={"xero_invoice_id": invoice.xero_invoice_id},
    )
    db.add(audit)
    await db.commit()
    logger.info(
        "Xero bill %s voided for invoice %s",
        invoice.xero_invoice_id,
        invoice_id,
    )


async def reconcile_xero_invoices(db: AsyncSession) -> dict:
    """Poll Xero for status updates on all APPROVED invoices.

    Updates any that have been PAID in Xero since the last check.
    Returns a summary dict with keys ``checked`` and ``updated``.
    """
    result = await db.execute(
        select(Invoice).where(
            Invoice.status == "APPROVED",
            Invoice.xero_invoice_id.isnot(None),
        )
    )
    invoices = result.scalars().all()

    if not invoices:
        return {"checked": 0, "updated": 0}

    client = await _get_xero_client(db)
    updated = 0

    for invoice in invoices:
        try:
            xero_bill = await client.get_bill(invoice.xero_invoice_id)
            if xero_bill.status == "PAID":
                await sync_payment_from_xero(db, invoice.xero_invoice_id)
                updated += 1
        except Exception:  # noqa: BLE001
            logger.exception(
                "Failed to reconcile invoice %s (xero_id=%s)",
                invoice.id,
                invoice.xero_invoice_id,
            )

    logger.info(
        "Xero reconciliation complete: checked=%s, updated=%s",
        len(invoices),
        updated,
    )
    return {"checked": len(invoices), "updated": updated}
