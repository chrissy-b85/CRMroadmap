"""Tests for the invoice validation service and workflow endpoints."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import pytest

from app.models.invoice import Invoice
from app.models.invoice_line_item import InvoiceLineItem
from app.models.participant import Plan, SupportCategory
from app.models.provider import Provider
from app.services.invoice_validation_service import (
    validate_budget_availability,
    validate_invoice,
    validate_not_duplicate,
    validate_ocr_confidence,
    validate_provider_abn,
    validate_unit_prices,
)

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _make_invoice(
    db_session,
    *,
    provider_id=None,
    plan_id=None,
    invoice_number="INV-TEST-001",
    invoice_date=date(2024, 7, 15),
    total_amount=Decimal("110.00"),
    gst_amount=Decimal("10.00"),
    ocr_confidence=Decimal("0.95"),
    status="QUEUED",
):
    invoice = Invoice(
        provider_id=provider_id,
        plan_id=plan_id,
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        total_amount=total_amount,
        gst_amount=gst_amount,
        ocr_confidence=ocr_confidence,
        status=status,
    )
    db_session.add(invoice)
    await db_session.flush()
    return invoice


async def _make_provider(db_session, abn="12345678901", is_active=True):
    provider = Provider(
        abn=abn,
        business_name="Test Provider Pty Ltd",
        is_active=is_active,
    )
    db_session.add(provider)
    await db_session.flush()
    return provider


# ---------------------------------------------------------------------------
# 1. test_validate_abn_match_passes
# ---------------------------------------------------------------------------


async def test_validate_abn_match_passes(db_session):
    """Known active provider ABN passes the ABN validation rule."""
    provider = await _make_provider(db_session, abn="11111111111")
    invoice = await _make_invoice(db_session, provider_id=provider.id)

    result = await validate_provider_abn(db_session, invoice)

    assert result.passed is True
    assert result.rule_name == "validate_provider_abn"
    assert result.severity == "error"


# ---------------------------------------------------------------------------
# 2. test_validate_abn_mismatch_fails
# ---------------------------------------------------------------------------


async def test_validate_abn_mismatch_fails(db_session):
    """Invoice with no matched provider fails ABN validation with an error."""
    invoice = await _make_invoice(db_session, provider_id=None)

    result = await validate_provider_abn(db_session, invoice)

    assert result.passed is False
    assert result.severity == "error"
    assert "ABN" in result.message or "provider" in result.message.lower()


# ---------------------------------------------------------------------------
# 3. test_validate_unit_price_within_limit_passes
# ---------------------------------------------------------------------------


async def test_validate_unit_price_within_limit_passes(db_session):
    """Line item unit price within NDIS limit passes unit price validation."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    invoice = await _make_invoice(db_session)
    line_item = InvoiceLineItem(
        invoice_id=invoice.id,
        support_item_number="07_001_0106_8_3",  # limit = 100.14
        unit_price=Decimal("100.00"),
        quantity=Decimal("1"),
        total=Decimal("100.00"),
    )
    db_session.add(line_item)
    await db_session.flush()

    result = await db_session.execute(
        select(Invoice)
        .options(selectinload(Invoice.line_items))
        .where(Invoice.id == invoice.id)
    )
    invoice = result.scalar_one()

    rule_result = await validate_unit_prices(db_session, invoice)

    assert rule_result.passed is True


# ---------------------------------------------------------------------------
# 4. test_validate_unit_price_exceeds_limit_fails
# ---------------------------------------------------------------------------


async def test_validate_unit_price_exceeds_limit_fails(db_session):
    """Line item unit price exceeding NDIS limit fails unit price validation."""
    invoice = await _make_invoice(db_session)
    line_item = InvoiceLineItem(
        invoice_id=invoice.id,
        support_item_number="07_001_0106_8_3",  # limit = 100.14
        unit_price=Decimal("200.00"),  # Exceeds limit
        quantity=Decimal("1"),
        total=Decimal("200.00"),
    )
    db_session.add(line_item)
    await db_session.flush()

    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    result = await db_session.execute(
        select(Invoice)
        .options(selectinload(Invoice.line_items))
        .where(Invoice.id == invoice.id)
    )
    invoice = result.scalar_one()

    rule_result = await validate_unit_prices(db_session, invoice)

    assert rule_result.passed is False
    assert rule_result.severity == "error"


# ---------------------------------------------------------------------------
# 5. test_validate_duplicate_invoice_fails
# ---------------------------------------------------------------------------


async def test_validate_duplicate_invoice_fails(db_session):
    """Duplicate provider+invoice_number combination fails duplicate check."""
    provider = await _make_provider(db_session, abn="22222222222")

    # Create the existing invoice
    await _make_invoice(
        db_session,
        provider_id=provider.id,
        invoice_number="DUP-001",
    )
    await db_session.commit()

    # Create new invoice with same provider + number
    new_invoice = await _make_invoice(
        db_session,
        provider_id=provider.id,
        invoice_number="DUP-001",
    )

    rule_result = await validate_not_duplicate(db_session, new_invoice)

    assert rule_result.passed is False
    assert rule_result.severity == "error"
    assert "DUP-001" in rule_result.message


# ---------------------------------------------------------------------------
# 6. test_validate_ocr_confidence_low_warns
# ---------------------------------------------------------------------------


async def test_validate_ocr_confidence_low_warns(db_session):
    """Low OCR confidence score produces a warning (not an error)."""
    invoice = await _make_invoice(db_session, ocr_confidence=Decimal("0.75"))

    rule_result = await validate_ocr_confidence(db_session, invoice)

    assert rule_result.passed is False
    assert rule_result.severity == "warning"  # Must be warning, not error


# ---------------------------------------------------------------------------
# 7. test_validate_budget_insufficient_fails
# ---------------------------------------------------------------------------


async def test_validate_budget_insufficient_fails(db_session):
    """Invoice that exceeds support category budget fails budget validation."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    # Create participant + plan + support category
    from app.models.participant import Participant

    participant = Participant(
        ndis_number=f"NDIS{uuid.uuid4().hex[:8].upper()}",
        first_name="Bob",
        last_name="Budget",
    )
    db_session.add(participant)
    await db_session.flush()

    plan = Plan(
        participant_id=participant.id,
        plan_start_date=date(2024, 7, 1),
        plan_end_date=date(2025, 6, 30),
        total_funding=Decimal("5000.00"),
        is_active=True,
    )
    db_session.add(plan)
    await db_session.flush()

    cat = SupportCategory(
        plan_id=plan.id,
        ndis_support_category="Support Coordination",
        budget_allocated=Decimal("100.00"),
        budget_spent=Decimal("90.00"),  # Only $10 remaining
    )
    db_session.add(cat)
    await db_session.flush()

    invoice = await _make_invoice(db_session)
    line_item = InvoiceLineItem(
        invoice_id=invoice.id,
        support_item_number="07_001_0106_8_3",
        unit_price=Decimal("50.00"),
        quantity=Decimal("1"),
        total=Decimal("50.00"),  # Exceeds the $10 remaining
        support_category_id=cat.id,
    )
    db_session.add(line_item)
    await db_session.flush()

    result = await db_session.execute(
        select(Invoice)
        .options(selectinload(Invoice.line_items))
        .where(Invoice.id == invoice.id)
    )
    invoice = result.scalar_one()

    rule_result = await validate_budget_availability(db_session, invoice)

    assert rule_result.passed is False
    assert rule_result.severity == "error"


# ---------------------------------------------------------------------------
# 8. test_full_validation_all_pass_sets_pending_approval
# ---------------------------------------------------------------------------


async def test_full_validation_all_pass_sets_pending_approval(db_session):
    """Full validation with all rules passing sets invoice to PENDING_APPROVAL."""
    from app.models.participant import Participant

    participant = Participant(
        ndis_number=f"NDIS{uuid.uuid4().hex[:8].upper()}",
        first_name="Alice",
        last_name="Pass",
    )
    db_session.add(participant)
    await db_session.flush()

    plan = Plan(
        participant_id=participant.id,
        plan_start_date=date(2024, 7, 1),
        plan_end_date=date(2025, 6, 30),
        total_funding=Decimal("50000.00"),
        is_active=True,
    )
    db_session.add(plan)
    await db_session.flush()

    cat = SupportCategory(
        plan_id=plan.id,
        ndis_support_category="Support Coordination",
        budget_allocated=Decimal("5000.00"),
        budget_spent=Decimal("0.00"),
    )
    db_session.add(cat)
    await db_session.flush()

    provider = await _make_provider(db_session, abn="33333333333")

    total = Decimal("110.00")
    gst = (total * Decimal("10") / Decimal("110")).quantize(Decimal("0.01"))
    invoice = await _make_invoice(
        db_session,
        provider_id=provider.id,
        plan_id=plan.id,
        invoice_number=f"PASS-{uuid.uuid4().hex[:6]}",
        invoice_date=date(2024, 9, 1),
        total_amount=total,
        gst_amount=gst,
        ocr_confidence=Decimal("0.95"),
    )

    line_item = InvoiceLineItem(
        invoice_id=invoice.id,
        support_item_number="07_001_0106_8_3",
        unit_price=Decimal("100.00"),
        quantity=Decimal("1"),
        total=Decimal("100.00"),
        support_category_id=cat.id,
    )
    db_session.add(line_item)
    await db_session.commit()

    report = await validate_invoice(db_session, invoice.id)

    assert report.final_status == "PENDING_APPROVAL"
    assert report.passed is True


# ---------------------------------------------------------------------------
# 9. test_full_validation_error_sets_flagged
# ---------------------------------------------------------------------------


async def test_full_validation_error_sets_flagged(db_session):
    """Full validation with an error rule failure sets invoice to FLAGGED."""
    # Invoice with no provider (ABN validation will fail with error)
    invoice = await _make_invoice(
        db_session,
        provider_id=None,
        invoice_number=f"FLAG-{uuid.uuid4().hex[:6]}",
    )
    await db_session.commit()

    report = await validate_invoice(db_session, invoice.id)

    assert report.final_status == "FLAGGED"
    assert report.passed is False
    # Verify at least one error-severity rule failed
    error_failures = [
        r for r in report.results if r.severity == "error" and not r.passed
    ]
    assert len(error_failures) > 0


# ---------------------------------------------------------------------------
# 10. test_approve_invoice_updates_budget_spent
# ---------------------------------------------------------------------------


async def test_approve_invoice_updates_budget_spent(test_client, db_session):
    """Approving a PENDING_APPROVAL invoice updates support category budget_spent."""
    from sqlalchemy import select

    from app.models.participant import Participant

    participant = Participant(
        ndis_number=f"NDIS{uuid.uuid4().hex[:8].upper()}",
        first_name="Charlie",
        last_name="Approve",
    )
    db_session.add(participant)
    await db_session.flush()

    plan = Plan(
        participant_id=participant.id,
        plan_start_date=date(2024, 7, 1),
        plan_end_date=date(2025, 6, 30),
        total_funding=Decimal("10000.00"),
        is_active=True,
    )
    db_session.add(plan)
    await db_session.flush()

    cat = SupportCategory(
        plan_id=plan.id,
        ndis_support_category="Daily Activities",
        budget_allocated=Decimal("2000.00"),
        budget_spent=Decimal("0.00"),
    )
    db_session.add(cat)
    await db_session.flush()

    invoice = Invoice(
        invoice_number=f"APPROVE-{uuid.uuid4().hex[:6]}",
        invoice_date=date(2024, 8, 1),
        total_amount=Decimal("550.00"),
        gst_amount=Decimal("50.00"),
        status="PENDING_APPROVAL",
    )
    db_session.add(invoice)
    await db_session.flush()

    line_item = InvoiceLineItem(
        invoice_id=invoice.id,
        unit_price=Decimal("550.00"),
        quantity=Decimal("1"),
        total=Decimal("550.00"),
        support_category_id=cat.id,
    )
    db_session.add(line_item)
    await db_session.commit()

    resp = await test_client.post(f"/api/v1/invoices/{invoice.id}/approve")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "APPROVED"

    # Verify budget_spent updated
    cat_result = await db_session.execute(
        select(SupportCategory).where(SupportCategory.id == cat.id)
    )
    updated_cat = cat_result.scalar_one()
    assert updated_cat.budget_spent == Decimal("550.00")


# ---------------------------------------------------------------------------
# 11. test_reject_invoice_sets_status
# ---------------------------------------------------------------------------


async def test_reject_invoice_sets_status(test_client, db_session):
    """Rejecting an invoice sets its status to REJECTED and stores the reason."""
    invoice = Invoice(
        invoice_number=f"REJECT-{uuid.uuid4().hex[:6]}",
        invoice_date=date(2024, 8, 1),
        total_amount=Decimal("200.00"),
        gst_amount=Decimal("20.00"),
        status="PENDING_APPROVAL",
    )
    db_session.add(invoice)
    await db_session.commit()

    resp = await test_client.post(
        f"/api/v1/invoices/{invoice.id}/reject",
        params={"reason": "Invalid support items"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "REJECTED"
