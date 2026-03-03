"""Tests for the Xero integration sync service and webhook handler."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.integrations.xero.client import XeroClient
from app.integrations.xero.models import XeroBill, XeroContact
from app.models.invoice import Invoice
from app.models.invoice_line_item import InvoiceLineItem
from app.models.provider import Provider
from app.models.xero_connection import XeroConnection

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _make_provider(db, abn="98765432100", xero_contact_id=None):
    provider = Provider(
        abn=abn,
        business_name="Xero Test Provider Pty Ltd",
        xero_contact_id=xero_contact_id,
    )
    db.add(provider)
    await db.flush()
    return provider


async def _make_invoice(db, provider_id=None, status="APPROVED", xero_invoice_id=None):
    invoice = Invoice(
        invoice_number=f"XINV-{uuid.uuid4().hex[:6]}",
        invoice_date=date(2024, 8, 1),
        total_amount=Decimal("110.00"),
        gst_amount=Decimal("10.00"),
        status=status,
        xero_invoice_id=xero_invoice_id,
        provider_id=provider_id,
    )
    db.add(invoice)
    await db.flush()
    return invoice


async def _make_xero_connection(db, is_active=True):
    conn = XeroConnection(
        tenant_id="test-tenant-id",
        access_token="test-access-token",
        refresh_token="test-refresh-token",
        token_expiry=datetime.now(tz=timezone.utc) + timedelta(hours=1),
        is_active=is_active,
    )
    db.add(conn)
    await db.flush()
    return conn


# ---------------------------------------------------------------------------
# 1. test_create_xero_contact_from_provider
# ---------------------------------------------------------------------------


async def test_create_xero_contact_from_provider(db_session):
    """XeroClient.create_contact sends correct payload and returns XeroContact."""
    provider = await _make_provider(db_session, abn="11122233344")

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "Contacts": [
            {
                "ContactID": "xero-contact-abc",
                "Name": provider.business_name,
                "TaxNumber": provider.abn,
            }
        ]
    }

    with patch("httpx.AsyncClient") as mock_http:
        mock_http.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )
        client = XeroClient(
            access_token="token", refresh_token="refresh", tenant_id="tenant"
        )
        contact = await client.create_contact(provider)

    assert contact.contact_id == "xero-contact-abc"
    assert contact.name == provider.business_name
    assert contact.tax_number == provider.abn


# ---------------------------------------------------------------------------
# 2. test_sync_approved_invoice_creates_xero_bill
# ---------------------------------------------------------------------------


async def test_sync_approved_invoice_creates_xero_bill(db_session):
    """sync_approved_invoice_to_xero calls create_bill with correct data."""
    await _make_xero_connection(db_session)
    provider = await _make_provider(
        db_session, abn="22233344455", xero_contact_id="existing-xero-contact"
    )
    invoice = await _make_invoice(db_session, provider_id=provider.id, status="APPROVED")
    line_item = InvoiceLineItem(
        invoice_id=invoice.id,
        description="Support service",
        quantity=Decimal("1"),
        unit_price=Decimal("100.00"),
        total=Decimal("100.00"),
    )
    db_session.add(line_item)
    await db_session.commit()

    mock_bill = XeroBill(
        xero_invoice_id="xero-bill-123",
        invoice_number=invoice.invoice_number,
        status="SUBMITTED",
        amount_due=Decimal("110.00"),
        amount_paid=Decimal("0.00"),
        contact_id="existing-xero-contact",
    )

    with patch(
        "app.services.xero_sync_service.XeroClient.create_bill",
        new_callable=AsyncMock,
        return_value=mock_bill,
    ):
        from app.services.xero_sync_service import sync_approved_invoice_to_xero

        xero_id = await sync_approved_invoice_to_xero(db_session, invoice.id)

    assert xero_id == "xero-bill-123"


# ---------------------------------------------------------------------------
# 3. test_sync_approved_invoice_stores_xero_id
# ---------------------------------------------------------------------------


async def test_sync_approved_invoice_stores_xero_id(db_session):
    """After sync, the CRM invoice has xero_invoice_id populated."""
    await _make_xero_connection(db_session)
    provider = await _make_provider(
        db_session, abn="33344455566", xero_contact_id="contact-xyz"
    )
    invoice = await _make_invoice(db_session, provider_id=provider.id, status="APPROVED")
    line_item = InvoiceLineItem(
        invoice_id=invoice.id,
        description="Item",
        quantity=Decimal("1"),
        unit_price=Decimal("50.00"),
        total=Decimal("50.00"),
    )
    db_session.add(line_item)
    await db_session.commit()

    mock_bill = XeroBill(
        xero_invoice_id="stored-xero-id-999",
        invoice_number=invoice.invoice_number,
        status="SUBMITTED",
        amount_due=Decimal("50.00"),
        amount_paid=Decimal("0.00"),
        contact_id="contact-xyz",
    )

    with patch(
        "app.services.xero_sync_service.XeroClient.create_bill",
        new_callable=AsyncMock,
        return_value=mock_bill,
    ):
        from app.services.xero_sync_service import sync_approved_invoice_to_xero

        await sync_approved_invoice_to_xero(db_session, invoice.id)

    from sqlalchemy import select

    result = await db_session.execute(
        select(Invoice).where(Invoice.id == invoice.id)
    )
    refreshed = result.scalar_one()
    assert refreshed.xero_invoice_id == "stored-xero-id-999"


# ---------------------------------------------------------------------------
# 4. test_xero_webhook_signature_validation
# ---------------------------------------------------------------------------


def test_xero_webhook_signature_validation():
    """validate_webhook_signature returns True for valid HMAC-SHA256 signature."""
    key = "my-secret-webhook-key"
    payload = b'{"events": []}'
    expected_sig = base64.b64encode(
        hmac.new(key.encode(), payload, hashlib.sha256).digest()
    ).decode()

    with patch("app.integrations.xero.client.XERO_WEBHOOK_KEY", key):
        result = XeroClient.validate_webhook_signature(payload, expected_sig)

    assert result is True


def test_xero_webhook_signature_validation_invalid():
    """validate_webhook_signature returns False for wrong signature."""
    key = "my-secret-webhook-key"
    payload = b'{"events": []}'

    with patch("app.integrations.xero.client.XERO_WEBHOOK_KEY", key):
        result = XeroClient.validate_webhook_signature(payload, "wrong-signature")

    assert result is False


# ---------------------------------------------------------------------------
# 5. test_xero_webhook_payment_updates_invoice_status
# ---------------------------------------------------------------------------


async def test_xero_webhook_payment_updates_invoice_status(db_session):
    """sync_payment_from_xero updates CRM invoice status to PAID."""
    invoice = await _make_invoice(
        db_session, status="APPROVED", xero_invoice_id="xero-pay-001"
    )
    await db_session.commit()

    from app.services.xero_sync_service import sync_payment_from_xero

    updated = await sync_payment_from_xero(db_session, "xero-pay-001")

    assert updated.status == "PAID"
    assert updated.id == invoice.id


# ---------------------------------------------------------------------------
# 6. test_reconcile_finds_paid_invoices
# ---------------------------------------------------------------------------


async def test_reconcile_finds_paid_invoices(db_session):
    """reconcile_xero_invoices updates invoices that Xero marks as PAID."""
    await _make_xero_connection(db_session)
    invoice = await _make_invoice(
        db_session, status="APPROVED", xero_invoice_id="xero-reconcile-111"
    )
    await db_session.commit()

    mock_bill = XeroBill(
        xero_invoice_id="xero-reconcile-111",
        invoice_number=invoice.invoice_number,
        status="PAID",
        amount_due=Decimal("0.00"),
        amount_paid=Decimal("110.00"),
        contact_id="",
    )

    with patch(
        "app.services.xero_sync_service.XeroClient.get_bill",
        new_callable=AsyncMock,
        return_value=mock_bill,
    ):
        from app.services.xero_sync_service import reconcile_xero_invoices

        summary = await reconcile_xero_invoices(db_session)

    assert summary["checked"] >= 1
    assert summary["updated"] >= 1

    from sqlalchemy import select

    result = await db_session.execute(
        select(Invoice).where(Invoice.id == invoice.id)
    )
    refreshed = result.scalar_one()
    assert refreshed.status == "PAID"


# ---------------------------------------------------------------------------
# 7. test_void_bill_on_rejection
# ---------------------------------------------------------------------------


async def test_void_bill_on_rejection(db_session):
    """void_xero_bill calls the Xero API to void the bill."""
    await _make_xero_connection(db_session)
    invoice = await _make_invoice(
        db_session, status="APPROVED", xero_invoice_id="xero-void-777"
    )
    await db_session.commit()

    with patch(
        "app.services.xero_sync_service.XeroClient.void_bill",
        new_callable=AsyncMock,
    ) as mock_void:
        from app.services.xero_sync_service import void_xero_bill

        await void_xero_bill(db_session, invoice.id)

    mock_void.assert_awaited_once_with("xero-void-777")
