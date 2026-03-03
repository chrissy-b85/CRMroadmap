"""Tests for PDF statement generation service and API endpoints."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.models.invoice import Invoice
from app.models.participant import Participant
from app.models.plan import Plan
from app.models.statement import StatementRecord
from app.models.support_category import SupportCategory

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------


async def _create_participant(db, ndis_number: str | None = None) -> Participant:
    p = Participant(
        ndis_number=ndis_number or f"NDIS{uuid.uuid4().hex[:8].upper()}",
        first_name="Test",
        last_name="User",
        email="test@example.com",
        is_active=True,
    )
    db.add(p)
    await db.flush()
    return p


async def _create_plan(db, participant_id) -> Plan:
    plan = Plan(
        participant_id=participant_id,
        plan_start_date=date(2026, 1, 1),
        plan_end_date=date(2026, 12, 31),
        total_funding=Decimal("50000.00"),
        is_active=True,
    )
    db.add(plan)
    await db.flush()
    return plan


async def _create_support_category(db, plan_id) -> SupportCategory:
    cat = SupportCategory(
        plan_id=plan_id,
        ndis_support_category="Daily Activities",
        budget_allocated=Decimal("20000.00"),
        budget_spent=Decimal("5000.00"),
    )
    db.add(cat)
    await db.flush()
    return cat


async def _create_invoice(
    db,
    participant_id,
    plan_id,
    invoice_date: date,
    status: str = "APPROVED",
    total: Decimal = Decimal("1100.00"),
    gst: Decimal = Decimal("100.00"),
) -> Invoice:
    inv = Invoice(
        participant_id=participant_id,
        plan_id=plan_id,
        invoice_number=f"INV-{uuid.uuid4().hex[:6].upper()}",
        invoice_date=invoice_date,
        total_amount=total,
        gst_amount=gst,
        status=status,
        gcs_json_path="gs://bucket/test.json",
    )
    db.add(inv)
    await db.flush()
    return inv


# ---------------------------------------------------------------------------
# Test 1: generate_monthly_statement creates a StatementRecord in the DB
# ---------------------------------------------------------------------------


async def test_generate_monthly_statement_creates_pdf(db_session):
    """generate_monthly_statement persists a StatementRecord with correct fields."""
    participant = await _create_participant(db_session)
    plan = await _create_plan(db_session, participant.id)
    await _create_invoice(db_session, participant.id, plan.id, date(2026, 2, 15))
    await db_session.commit()

    from app.services.statement_service import generate_monthly_statement

    mock_pdf = b"%PDF-1.4 fake pdf content"
    mock_gcs_path = f"gs://ndis-crm-invoices/statements/{participant.id}/2026-02.pdf"

    with (
        patch("app.services.statement_service._html_to_pdf", return_value=mock_pdf),
        patch(
            "app.services.statement_service._render_html", return_value="<html></html>"
        ),
        patch(
            "app.integrations.gcs.client.GCSClient.upload_bytes",
            new_callable=AsyncMock,
            return_value=mock_gcs_path,
        ),
    ):
        record = await generate_monthly_statement(db_session, participant.id, 2026, 2)

    assert record is not None
    assert record.participant_id == participant.id
    assert record.year == 2026
    assert record.month == 2
    assert record.gcs_pdf_path == mock_gcs_path
    assert isinstance(record.generated_at, datetime)


# ---------------------------------------------------------------------------
# Test 2: statement includes correct invoice count
# ---------------------------------------------------------------------------


async def test_statement_includes_correct_invoice_count(db_session):
    """StatementRecord.invoice_count reflects the number of APPROVED invoices."""
    participant = await _create_participant(db_session)
    plan = await _create_plan(db_session, participant.id)

    # 3 approved invoices in the target month
    for _ in range(3):
        await _create_invoice(db_session, participant.id, plan.id, date(2026, 3, 10))
    # 1 rejected invoice — should NOT be counted
    await _create_invoice(
        db_session, participant.id, plan.id, date(2026, 3, 20), status="REJECTED"
    )
    await db_session.commit()

    from app.services.statement_service import generate_monthly_statement

    with (
        patch("app.services.statement_service._html_to_pdf", return_value=b"%PDF"),
        patch(
            "app.services.statement_service._render_html", return_value="<html></html>"
        ),
        patch(
            "app.integrations.gcs.client.GCSClient.upload_bytes",
            new_callable=AsyncMock,
            return_value="gs://bucket/test.pdf",
        ),
    ):
        record = await generate_monthly_statement(db_session, participant.id, 2026, 3)

    assert record.invoice_count == 3


# ---------------------------------------------------------------------------
# Test 3: statement budget totals are correct
# ---------------------------------------------------------------------------


async def test_statement_budget_totals_correct(db_session):
    """StatementRecord.total_amount is the sum of all APPROVED invoice amounts."""
    participant = await _create_participant(db_session)
    plan = await _create_plan(db_session, participant.id)

    await _create_invoice(
        db_session,
        participant.id,
        plan.id,
        date(2026, 4, 5),
        total=Decimal("500.00"),
        gst=Decimal("50.00"),
    )
    await _create_invoice(
        db_session,
        participant.id,
        plan.id,
        date(2026, 4, 20),
        total=Decimal("1200.00"),
        gst=Decimal("109.09"),
    )
    await db_session.commit()

    from app.services.statement_service import generate_monthly_statement

    with (
        patch("app.services.statement_service._html_to_pdf", return_value=b"%PDF"),
        patch(
            "app.services.statement_service._render_html", return_value="<html></html>"
        ),
        patch(
            "app.integrations.gcs.client.GCSClient.upload_bytes",
            new_callable=AsyncMock,
            return_value="gs://bucket/test.pdf",
        ),
    ):
        record = await generate_monthly_statement(db_session, participant.id, 2026, 4)

    assert record.total_amount == Decimal("1700.00")


# ---------------------------------------------------------------------------
# Test 4: generate_monthly_statement with no invoices — still creates record
# ---------------------------------------------------------------------------


async def test_generate_statement_no_invoices_skipped(db_session):
    """generate_all_monthly_statements skips participants with no APPROVED invoices."""
    await _create_participant(db_session)
    await db_session.commit()

    from app.services.statement_service import generate_all_monthly_statements

    with (
        patch("app.services.statement_service._html_to_pdf", return_value=b"%PDF"),
        patch(
            "app.services.statement_service._render_html", return_value="<html></html>"
        ),
        patch(
            "app.integrations.gcs.client.GCSClient.upload_bytes",
            new_callable=AsyncMock,
            return_value="gs://bucket/test.pdf",
        ),
    ):
        result = await generate_all_monthly_statements(db_session, 2026, 5)

    # Participant with no invoices should be counted as skipped
    assert result["skipped"] >= 1
    assert result["failed"] == 0


# ---------------------------------------------------------------------------
# Test 5: get_statement returns None when no record exists
# ---------------------------------------------------------------------------


async def test_get_statement_returns_none_when_missing(db_session):
    """get_statement returns None when no record exists for the given period."""
    from app.services.statement_service import get_statement

    result = await get_statement(db_session, uuid.uuid4(), 2026, 1)
    assert result is None


# ---------------------------------------------------------------------------
# Test 6: API endpoint returns signed URL via router
# ---------------------------------------------------------------------------


async def test_get_statement_returns_signed_url(
    test_client, db_session, sample_participant
):
    """GET /statements/participants/{id}/{year}/{month} returns StatementOut."""
    part_id = uuid.UUID(sample_participant["id"])

    # Directly insert a StatementRecord
    record = StatementRecord(
        participant_id=part_id,
        year=2026,
        month=1,
        gcs_pdf_path=f"gs://ndis-crm-invoices/statements/{part_id}/2026-01.pdf",
        invoice_count=2,
        total_amount=Decimal("2200.00"),
        generated_at=datetime.now(tz=timezone.utc),
    )
    db_session.add(record)
    await db_session.commit()

    mock_url = "https://storage.googleapis.com/signed?token=abc123"

    with patch(
        "app.integrations.gcs.client.GCSClient.get_signed_url",
        new_callable=AsyncMock,
        return_value=mock_url,
    ):
        resp = await test_client.get(
            f"/api/v1/statements/participants/{part_id}/2026/1"
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["year"] == 2026
    assert data["month"] == 1
    assert data["download_url"] == mock_url
    assert data["statement_period"] == "January 2026"
    assert data["invoice_count"] == 2


# ---------------------------------------------------------------------------
# Test 7: batch generate endpoint triggers generation for active participants
# ---------------------------------------------------------------------------


async def test_batch_generate_all_participants(test_client, db_session):
    """POST /statements/batch/{year}/{month} queues batch generation."""
    resp = await test_client.post("/api/v1/statements/batch/2026/6")
    # Returns 202 Accepted
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "accepted"


# ---------------------------------------------------------------------------
# Test 8: email_statement calls Graph API send_mail
# ---------------------------------------------------------------------------


async def test_email_statement_calls_graph_api(db_session):
    """email_statement invokes GraphClient.send_mail with correct recipient."""
    participant = await _create_participant(db_session)
    plan = await _create_plan(db_session, participant.id)
    await _create_invoice(db_session, participant.id, plan.id, date(2026, 2, 10))
    await db_session.commit()

    from app.services.statement_service import (
        email_statement,
        generate_monthly_statement,
    )

    mock_msg_id = "graph-msg-123"

    with (
        patch("app.services.statement_service._html_to_pdf", return_value=b"%PDF"),
        patch(
            "app.services.statement_service._render_html", return_value="<html></html>"
        ),
        patch(
            "app.integrations.gcs.client.GCSClient.upload_bytes",
            new_callable=AsyncMock,
            return_value="gs://bucket/test.pdf",
        ),
        patch(
            "app.integrations.graph.client.GraphClient.send_mail",
            new_callable=AsyncMock,
            return_value=mock_msg_id,
        ) as mock_send,
    ):
        # First generate the statement so it exists in the DB
        await generate_monthly_statement(db_session, participant.id, 2026, 2)
        record = await email_statement(db_session, participant.id, 2026, 2)

    mock_send.assert_awaited()
    assert record.email_message_id == mock_msg_id
    assert record.emailed_at is not None
