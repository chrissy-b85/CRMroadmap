"""Tests for participant invoice approval/query endpoints."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.auth.participant import get_current_participant
from app.db import Base, get_db
from app.models.invoice import Invoice
from app.models.participant import Participant
import app.models.push_subscription  # noqa: F401 — register model before create_all

pytestmark = pytest.mark.asyncio

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_participant(**kwargs) -> Participant:
    defaults = dict(
        ndis_number=f"NDIS{uuid.uuid4().hex[:8].upper()}",
        first_name="Test",
        last_name="User",
        auth0_sub=f"auth0|{uuid.uuid4().hex}",
    )
    defaults.update(kwargs)
    return Participant(**defaults)


def _make_invoice(participant_id, **kwargs) -> Invoice:
    defaults = dict(
        invoice_date=date(2024, 7, 1),
        total_amount=Decimal("550.00"),
        gst_amount=Decimal("50.00"),
        status="PENDING_APPROVAL",
        gcs_json_path="gs://bucket/test.json",
    )
    defaults.update(kwargs)
    return Invoice(participant_id=participant_id, **defaults)


async def _make_participant_client(app, db_session, participant: Participant):
    """Create an AsyncClient with get_current_participant overridden."""

    async def override_get_db():
        yield db_session

    async def override_get_current_participant():
        return participant

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_participant] = override_get_current_participant
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ---------------------------------------------------------------------------
# 1. test_participant_can_approve_own_invoice
# ---------------------------------------------------------------------------


async def test_participant_can_approve_own_invoice(db_session):
    """A participant can approve an invoice that belongs to them."""
    from main import app

    participant = _make_participant()
    db_session.add(participant)
    await db_session.flush()

    invoice = _make_invoice(participant.id)
    db_session.add(invoice)
    await db_session.commit()
    await db_session.refresh(invoice)

    async with await _make_participant_client(app, db_session, participant) as client:
        resp = await client.post(f"/api/v1/invoices/{invoice.id}/participant-approve")

    app.dependency_overrides.clear()

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["participant_approved"] is True
    assert body["participant_approved_at"] is not None
    assert body["status"] == "PENDING_APPROVAL"


# ---------------------------------------------------------------------------
# 2. test_participant_cannot_approve_other_participant_invoice
# ---------------------------------------------------------------------------


async def test_participant_cannot_approve_other_participant_invoice(db_session):
    """A participant gets 403 when trying to approve another participant's invoice."""
    from main import app

    owner = _make_participant()
    other = _make_participant()
    db_session.add_all([owner, other])
    await db_session.flush()

    invoice = _make_invoice(owner.id)
    db_session.add(invoice)
    await db_session.commit()
    await db_session.refresh(invoice)

    async with await _make_participant_client(app, db_session, other) as client:
        resp = await client.post(f"/api/v1/invoices/{invoice.id}/participant-approve")

    app.dependency_overrides.clear()

    assert resp.status_code == 403, resp.text


# ---------------------------------------------------------------------------
# 3. test_participant_query_sets_info_requested_status
# ---------------------------------------------------------------------------


async def test_participant_query_sets_info_requested_status(db_session):
    """Querying an invoice sets status to INFO_REQUESTED and records the message."""
    from main import app

    participant = _make_participant()
    db_session.add(participant)
    await db_session.flush()

    invoice = _make_invoice(participant.id)
    db_session.add(invoice)
    await db_session.commit()
    await db_session.refresh(invoice)

    async with await _make_participant_client(app, db_session, participant) as client:
        resp = await client.post(
            f"/api/v1/invoices/{invoice.id}/participant-query",
            params={"message": "Line item 3 looks wrong"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "INFO_REQUESTED"
    assert body["participant_query_message"] == "Line item 3 looks wrong"


# ---------------------------------------------------------------------------
# 4. test_participant_approval_logged_in_audit
# ---------------------------------------------------------------------------


async def test_participant_approval_logged_in_audit(db_session):
    """Approving an invoice writes an audit log entry."""
    from sqlalchemy import select

    from app.models.audit_log import AuditLog
    from main import app

    participant = _make_participant()
    db_session.add(participant)
    await db_session.flush()

    invoice = _make_invoice(participant.id)
    db_session.add(invoice)
    await db_session.commit()
    await db_session.refresh(invoice)

    async with await _make_participant_client(app, db_session, participant) as client:
        resp = await client.post(f"/api/v1/invoices/{invoice.id}/participant-approve")

    app.dependency_overrides.clear()

    assert resp.status_code == 200, resp.text

    audit_result = await db_session.execute(
        select(AuditLog).where(
            AuditLog.entity_id == invoice.id,
            AuditLog.action == "participant_invoice_approved",
        )
    )
    entries = audit_result.scalars().all()
    assert len(entries) >= 1
    assert entries[0].entity_type == "Invoice"
    assert entries[0].new_values["participant_id"] == str(participant.id)


# ---------------------------------------------------------------------------
# 5. test_get_my_invoices_returns_only_own
# ---------------------------------------------------------------------------


async def test_get_my_invoices_returns_only_own(db_session):
    """GET /invoices/my-invoices returns only the participant's own invoices."""
    from main import app

    p1 = _make_participant()
    p2 = _make_participant()
    db_session.add_all([p1, p2])
    await db_session.flush()

    inv1 = _make_invoice(p1.id, invoice_date=date(2024, 8, 1))
    inv2 = _make_invoice(p2.id, invoice_date=date(2024, 8, 2))
    db_session.add_all([inv1, inv2])
    await db_session.commit()

    async with await _make_participant_client(app, db_session, p1) as client:
        resp = await client.get("/api/v1/invoices/my-invoices")

    app.dependency_overrides.clear()

    assert resp.status_code == 200, resp.text
    body = resp.json()
    ids = [item["id"] for item in body["items"]]
    assert str(inv1.id) in ids
    assert str(inv2.id) not in ids
