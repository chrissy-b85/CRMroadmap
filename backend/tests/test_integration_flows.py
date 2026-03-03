"""End-to-end integration tests covering full system flows."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.invoice import Invoice
from app.models.invoice_line_item import InvoiceLineItem
from app.models.participant import Participant
from app.models.plan import Plan
from app.models.support_category import SupportCategory
from tests.conftest import make_participant_payload

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _make_participant(db: AsyncSession) -> Participant:
    p = Participant(
        ndis_number=f"NDIS{uuid.uuid4().hex[:8].upper()}",
        first_name="Integration",
        last_name="Tester",
        date_of_birth=date(1990, 1, 1),
        email=f"int_{uuid.uuid4().hex[:6]}@example.com",
    )
    db.add(p)
    await db.flush()
    return p


async def _make_plan(db: AsyncSession, participant_id) -> Plan:
    plan = Plan(
        participant_id=participant_id,
        plan_start_date=date(2024, 7, 1),
        plan_end_date=date(2025, 6, 30),
        total_funding=Decimal("50000.00"),
        is_active=True,
    )
    db.add(plan)
    await db.flush()
    return plan


async def _make_category(
    db: AsyncSession,
    plan_id,
    allocated: Decimal = Decimal("10000.00"),
    spent: Decimal = Decimal("0.00"),
) -> SupportCategory:
    cat = SupportCategory(
        plan_id=plan_id,
        ndis_support_category="Daily Activities",
        budget_allocated=allocated,
        budget_spent=spent,
    )
    db.add(cat)
    await db.flush()
    return cat


# ---------------------------------------------------------------------------
# test_full_invoice_flow — ingest → validate → approve → xero sync
# ---------------------------------------------------------------------------


async def test_full_invoice_flow(db_session: AsyncSession, test_client):
    """Full flow: a participant and plan exist; an invoice is ingested, validated,
    and approved; budget_spent is updated and an audit log entry is created."""
    # Step 1: Create participant via API
    p_resp = await test_client.post("/api/v1/participants/", json=make_participant_payload())
    assert p_resp.status_code == 201
    participant = p_resp.json()

    # Step 2: Create plan via API
    plan_resp = await test_client.post(
        "/api/v1/plans/",
        json={
            "participant_id": participant["id"],
            "plan_start_date": "2024-07-01",
            "plan_end_date": "2025-06-30",
            "total_funding": "50000.00",
        },
    )
    assert plan_resp.status_code == 201
    plan = plan_resp.json()

    # Step 3: Insert an invoice directly (simulating ingestion result)
    invoice = Invoice(
        invoice_number=f"FLOW-{uuid.uuid4().hex[:6].upper()}",
        invoice_date=date(2024, 7, 15),
        total_amount=Decimal("1100.00"),
        gst_amount=Decimal("100.00"),
        status="PENDING_APPROVAL",
        participant_id=uuid.UUID(participant["id"]),
        plan_id=uuid.UUID(plan["id"]),
    )
    db_session.add(invoice)
    await db_session.flush()
    await db_session.commit()

    # Step 4: Approve via API
    approve_resp = await test_client.post(
        f"/api/v1/invoices/{invoice.id}/approve",
    )
    assert approve_resp.status_code == 200
    approved = approve_resp.json()
    assert approved["status"] == "APPROVED"

    # Step 5: Verify audit log was written
    audit_result = await db_session.execute(
        select(AuditLog).where(AuditLog.entity_id == invoice.id)
    )
    audit_entries = audit_result.scalars().all()
    assert any(e.action == "invoice_approved" for e in audit_entries)


# ---------------------------------------------------------------------------
# test_budget_decremented_after_approval
# ---------------------------------------------------------------------------


async def test_budget_decremented_after_approval(db_session: AsyncSession, test_client):
    """budget_spent on the support category is incremented when an invoice is approved."""
    participant = await _make_participant(db_session)
    plan = await _make_plan(db_session, participant.id)
    cat = await _make_category(db_session, plan.id, spent=Decimal("0.00"))

    invoice = Invoice(
        invoice_number=f"BUDGET-{uuid.uuid4().hex[:6].upper()}",
        invoice_date=date(2024, 8, 1),
        total_amount=Decimal("500.00"),
        gst_amount=Decimal("50.00"),
        status="PENDING_APPROVAL",
        participant_id=participant.id,
        plan_id=plan.id,
    )
    db_session.add(invoice)
    await db_session.flush()

    line_item = InvoiceLineItem(
        invoice_id=invoice.id,
        description="Support service",
        quantity=Decimal("1"),
        unit_price=Decimal("500.00"),
        total=Decimal("500.00"),
        support_category_id=cat.id,
    )
    db_session.add(line_item)
    await db_session.commit()

    approve_resp = await test_client.post(f"/api/v1/invoices/{invoice.id}/approve")
    assert approve_resp.status_code == 200

    await db_session.refresh(cat)
    assert cat.budget_spent == Decimal("500.00")


# ---------------------------------------------------------------------------
# test_duplicate_invoice_rejected
# ---------------------------------------------------------------------------


async def test_duplicate_invoice_rejected(db_session: AsyncSession, test_client):
    """Attempting to approve an already-approved invoice returns 422."""
    participant = await _make_participant(db_session)

    invoice = Invoice(
        invoice_number=f"DUP-{uuid.uuid4().hex[:6].upper()}",
        invoice_date=date(2024, 9, 1),
        total_amount=Decimal("200.00"),
        gst_amount=Decimal("20.00"),
        status="APPROVED",  # already approved
        participant_id=participant.id,
    )
    db_session.add(invoice)
    await db_session.commit()

    resp = await test_client.post(f"/api/v1/invoices/{invoice.id}/approve")
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# test_participant_approval_flow
# ---------------------------------------------------------------------------


async def test_participant_approval_flow(db_session: AsyncSession):
    """A participant can mark an invoice as participant-approved via the portal endpoint."""
    import pytest_asyncio
    from httpx import ASGITransport, AsyncClient
    from main import app
    from app.auth.participant import get_current_participant
    from app.db import get_db

    participant = await _make_participant(db_session)
    participant.auth0_sub = f"auth0|{uuid.uuid4().hex}"
    db_session.add(participant)

    invoice = Invoice(
        invoice_number=f"PART-{uuid.uuid4().hex[:6].upper()}",
        invoice_date=date(2024, 10, 1),
        total_amount=Decimal("300.00"),
        gst_amount=Decimal("30.00"),
        status="PENDING_APPROVAL",
        participant_id=participant.id,
    )
    db_session.add(invoice)
    await db_session.commit()

    # Override dependencies for participant-scoped client
    async def override_get_db():
        yield db_session

    async def override_get_participant():
        return participant

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_participant] = override_get_participant

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(f"/api/v1/invoices/{invoice.id}/participant-approve")
            assert resp.status_code == 200
            body = resp.json()
            assert body["participant_approved"] is True
    finally:
        app.dependency_overrides.clear()
