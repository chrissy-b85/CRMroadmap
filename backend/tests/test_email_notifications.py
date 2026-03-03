"""Tests for email notification service and correspondence monitoring."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.models.participant import Participant
from app.models.provider import Provider

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helper stubs
# ---------------------------------------------------------------------------


def _make_invoice(
    invoice_number: str = "INV-TEST-001",
    invoice_date: date | None = None,
    total_amount: Decimal = Decimal("1100.00"),
    status: str = "PENDING_APPROVAL",
):
    """Return a lightweight invoice-like namespace for testing."""
    return type(
        "_Invoice",
        (),
        {
            "id": uuid.uuid4(),
            "invoice_number": invoice_number,
            "invoice_date": invoice_date or date(2024, 7, 1),
            "total_amount": total_amount,
            "status": status,
            "provider_id": None,
            "participant_id": None,
        },
    )()


def _make_plan(
    plan_start_date: date | None = None,
    plan_end_date: date | None = None,
    total_funding: Decimal = Decimal("50000.00"),
):
    return type(
        "_Plan",
        (),
        {
            "id": uuid.uuid4(),
            "plan_start_date": plan_start_date or date(2024, 7, 1),
            "plan_end_date": plan_end_date or date(2025, 6, 30),
            "total_funding": total_funding,
        },
    )()


# ---------------------------------------------------------------------------
# 1. test_send_invoice_approved_notification_calls_graph
# ---------------------------------------------------------------------------


async def test_send_invoice_approved_notification_calls_graph():
    """EmailNotificationService.send_invoice_approved_notification calls Graph send_email."""
    from app.services.email_notification_service import EmailNotificationService

    with patch(
        "app.services.email_notification_service.GraphClient"
    ) as MockGraph:
        mock_client = AsyncMock()
        mock_client.send_email.return_value = "graph-msg-id-approve"
        MockGraph.return_value = mock_client

        svc = EmailNotificationService()
        invoice = _make_invoice()
        result = await svc.send_invoice_approved_notification(
            recipient_email="alice@example.com",
            participant_name="Alice Smith",
            invoice=invoice,
        )

    mock_client.send_email.assert_awaited_once()
    call_kwargs = mock_client.send_email.call_args
    assert "alice@example.com" in call_kwargs[1]["to_emails"]
    assert "Approved" in call_kwargs[1]["subject"]
    assert result == "graph-msg-id-approve"


# ---------------------------------------------------------------------------
# 2. test_send_plan_expiry_warning_calls_graph
# ---------------------------------------------------------------------------


async def test_send_plan_expiry_warning_calls_graph():
    """EmailNotificationService.send_plan_expiry_warning calls Graph send_email."""
    from app.services.email_notification_service import EmailNotificationService

    with patch(
        "app.services.email_notification_service.GraphClient"
    ) as MockGraph:
        mock_client = AsyncMock()
        mock_client.send_email.return_value = "graph-msg-id-expiry"
        MockGraph.return_value = mock_client

        svc = EmailNotificationService()
        plan = _make_plan()
        result = await svc.send_plan_expiry_warning(
            participant_email="bob@example.com",
            participant_name="Bob Jones",
            plan=plan,
            days_remaining=25,
        )

    mock_client.send_email.assert_awaited_once()
    call_kwargs = mock_client.send_email.call_args
    assert "bob@example.com" in call_kwargs[1]["to_emails"]
    assert "25" in call_kwargs[1]["subject"]
    assert result == "graph-msg-id-expiry"


# ---------------------------------------------------------------------------
# 3. test_send_low_budget_alert_calls_graph
# ---------------------------------------------------------------------------


async def test_send_low_budget_alert_calls_graph():
    """EmailNotificationService.send_low_budget_alert calls Graph send_email."""
    from app.services.email_notification_service import EmailNotificationService

    with patch(
        "app.services.email_notification_service.GraphClient"
    ) as MockGraph:
        mock_client = AsyncMock()
        mock_client.send_email.return_value = "graph-msg-id-budget"
        MockGraph.return_value = mock_client

        svc = EmailNotificationService()
        result = await svc.send_low_budget_alert(
            participant_email="carol@example.com",
            participant_name="Carol White",
            category_name="Daily Activities",
            utilisation_percent=76.5,
        )

    mock_client.send_email.assert_awaited_once()
    call_kwargs = mock_client.send_email.call_args
    assert "carol@example.com" in call_kwargs[1]["to_emails"]
    assert "Daily Activities" in call_kwargs[1]["subject"]
    assert result == "graph-msg-id-budget"


# ---------------------------------------------------------------------------
# 4. test_poll_correspondence_creates_email_thread
# ---------------------------------------------------------------------------


async def test_poll_correspondence_creates_email_thread(db_session):
    """poll_correspondence_inbox creates EmailThread records for each message."""
    from sqlalchemy import select

    from app.models.email_thread import EmailThread
    from app.services.correspondence_service import poll_correspondence_inbox

    fake_messages = [
        {
            "id": f"msg-corr-{uuid.uuid4().hex[:8]}",
            "conversationId": "conv-001",
            "subject": "Query about services",
            "from": {"emailAddress": {"address": "unknown@external.com", "name": "Unknown Sender"}},
            "receivedDateTime": "2024-09-01T10:00:00Z",
            "bodyPreview": "Hello, I have a question...",
            "hasAttachments": False,
        }
    ]

    with (
        patch(
            "app.services.correspondence_service.GraphClient"
        ) as MockGraph,
    ):
        mock_graph = AsyncMock()
        mock_graph.get_correspondence_folder_messages.return_value = fake_messages
        mock_graph.mark_message_as_read.return_value = None
        mock_graph.move_message_to_folder.return_value = None
        MockGraph.return_value = mock_graph

        result = await poll_correspondence_inbox(db_session)

    assert result["processed"] == 1

    threads_result = await db_session.execute(
        select(EmailThread).where(
            EmailThread.sender_email == "unknown@external.com"
        )
    )
    threads = threads_result.scalars().all()
    assert len(threads) == 1
    thread = threads[0]
    assert thread.subject == "Query about services"
    assert thread.direction == "inbound"
    assert thread.body_preview == "Hello, I have a question..."


# ---------------------------------------------------------------------------
# 5. test_match_sender_to_participant_by_email
# ---------------------------------------------------------------------------


async def test_match_sender_to_participant_by_email(db_session):
    """match_sender_to_record returns ('participant', id) for a known participant email."""
    from app.services.correspondence_service import match_sender_to_record

    participant = Participant(
        ndis_number=f"NDIS{uuid.uuid4().hex[:8].upper()}",
        first_name="Dana",
        last_name="Green",
        email="dana.green@example.com",
    )
    db_session.add(participant)
    await db_session.commit()
    await db_session.refresh(participant)

    match = await match_sender_to_record(db_session, "dana.green@example.com")
    assert match is not None
    record_type, record_id = match
    assert record_type == "participant"
    assert record_id == participant.id


# ---------------------------------------------------------------------------
# 6. test_match_sender_to_provider_by_email
# ---------------------------------------------------------------------------


async def test_match_sender_to_provider_by_email(db_session):
    """match_sender_to_record returns ('provider', id) for a known provider email."""
    from app.services.correspondence_service import match_sender_to_record

    provider = Provider(
        abn=f"{uuid.uuid4().int % 10**11:011d}",
        business_name="Acme Supports",
        email="billing@acmesupports.com.au",
    )
    db_session.add(provider)
    await db_session.commit()
    await db_session.refresh(provider)

    match = await match_sender_to_record(db_session, "billing@acmesupports.com.au")
    assert match is not None
    record_type, record_id = match
    assert record_type == "provider"
    assert record_id == provider.id


# ---------------------------------------------------------------------------
# 7. test_unmatched_sender_logged_unmatched
# ---------------------------------------------------------------------------


async def test_unmatched_sender_logged_unmatched(db_session):
    """poll_correspondence_inbox counts unmatched senders correctly."""
    from app.services.correspondence_service import poll_correspondence_inbox

    fake_messages = [
        {
            "id": f"msg-unmatched-{uuid.uuid4().hex[:8]}",
            "conversationId": "conv-unmatched",
            "subject": "Random email",
            "from": {"emailAddress": {"address": "nobody@nowhere.example", "name": None}},
            "receivedDateTime": "2024-09-02T12:00:00Z",
            "bodyPreview": None,
            "hasAttachments": False,
        }
    ]

    with patch(
        "app.services.correspondence_service.GraphClient"
    ) as MockGraph:
        mock_graph = AsyncMock()
        mock_graph.get_correspondence_folder_messages.return_value = fake_messages
        mock_graph.mark_message_as_read.return_value = None
        mock_graph.move_message_to_folder.return_value = None
        MockGraph.return_value = mock_graph

        result = await poll_correspondence_inbox(db_session)

    assert result["processed"] == 1
    assert result["matched"] == 0
    assert result["unmatched"] == 1
