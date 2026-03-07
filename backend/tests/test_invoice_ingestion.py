"""Tests for the invoice ingestion pipeline with mocked external services."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.integrations.document_ai.parser import (
    InvoiceLineItemParsed,
    InvoiceParseResult,
    parse_document_ai_response,
)
from app.models.invoice import Invoice
from app.models.invoice_line_item import InvoiceLineItem
from app.models.provider import Provider

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# 1. test_parse_document_ai_response
# ---------------------------------------------------------------------------


async def test_parse_document_ai_response():
    """parse_document_ai_response correctly extracts invoice fields."""
    sample_response = {
        "document": {
            "entities": [
                {"type_": "supplier_name", "mentionText": "Acme Support Pty Ltd", "confidence": 0.97},
                {"type_": "supplier_tax_id", "mentionText": "12 345 678 901", "confidence": 0.95},
                {"type_": "invoice_id", "mentionText": "INV-2024-001", "confidence": 0.99},
                {"type_": "invoice_date", "mentionText": "2024-07-01", "confidence": 0.98},
                {"type_": "due_date", "mentionText": "2024-07-31", "confidence": 0.96},
                {"type_": "total_amount", "mentionText": "$1,100.00", "confidence": 0.99},
                {"type_": "total_tax_amount", "mentionText": "$100.00", "confidence": 0.97},
                {
                    "type_": "line_item",
                    "mentionText": "Support coordination",
                    "confidence": 0.95,
                    "properties": [
                        {"type_": "line_item/description", "mentionText": "Support coordination"},
                        {"type_": "line_item/quantity", "mentionText": "2"},
                        {"type_": "line_item/unit_price", "mentionText": "$500.00"},
                        {"type_": "line_item/amount", "mentionText": "$1,000.00"},
                        {"type_": "line_item/product_code", "mentionText": "07_002_0106_8_3"},
                    ],
                },
            ]
        }
    }

    result = parse_document_ai_response(sample_response)

    assert result.supplier_name == "Acme Support Pty Ltd"
    assert result.supplier_abn == "12 345 678 901"
    assert result.invoice_number == "INV-2024-001"
    assert result.invoice_date == date(2024, 7, 1)
    assert result.due_date == date(2024, 7, 31)
    assert result.total_amount == Decimal("1100.00")
    assert result.gst_amount == Decimal("100.00")
    assert len(result.line_items) == 1
    item = result.line_items[0]
    assert item.description == "Support coordination"
    assert item.quantity == Decimal("2")
    assert item.unit_price == Decimal("500.00")
    assert item.total == Decimal("1000.00")
    assert item.support_item_number == "07_002_0106_8_3"
    assert result.confidence_score == 0.97


# ---------------------------------------------------------------------------
# 2. test_match_provider_by_abn_found
# ---------------------------------------------------------------------------


async def test_match_provider_by_abn_found(db_session):
    """match_provider_by_abn returns the matching provider when ABN exists."""
    from app.services.invoice_ingestion_service import match_provider_by_abn

    provider = Provider(
        abn="12345678901",
        name="Test Provider",
    )
    db_session.add(provider)
    await db_session.commit()
    await db_session.refresh(provider)

    found = await match_provider_by_abn(db_session, "12345678901")
    assert found is not None
    assert found.id == provider.id
    assert found.name == "Test Provider"


# ---------------------------------------------------------------------------
# 3. test_match_provider_by_abn_not_found
# ---------------------------------------------------------------------------


async def test_match_provider_by_abn_not_found(db_session):
    """match_provider_by_abn returns None for an unknown ABN."""
    from app.services.invoice_ingestion_service import match_provider_by_abn

    result = await match_provider_by_abn(db_session, "99999999999")
    assert result is None


# ---------------------------------------------------------------------------
# 4. test_process_invoice_email_creates_record
# ---------------------------------------------------------------------------


async def test_process_invoice_email_creates_record(db_session):
    """process_invoice_email creates Invoice and InvoiceLineItem DB records."""
    from app.services.invoice_ingestion_service import process_invoice_email

    fake_parse_result = InvoiceParseResult(
        supplier_name="Acme Support",
        supplier_abn=None,
        invoice_number="INV-001",
        invoice_date=date(2024, 7, 1),
        due_date=None,
        total_amount=Decimal("550.00"),
        gst_amount=Decimal("50.00"),
        line_items=[
            InvoiceLineItemParsed(
                description="Daily activities",
                quantity=Decimal("1"),
                unit_price=Decimal("500.00"),
                total=Decimal("500.00"),
            )
        ],
        confidence_score=0.95,
        raw_response={"document": {"entities": []}},
    )

    fake_message = {
        "id": "msg-abc-123",
        "conversationId": "conv-abc-123",
        "subject": "Invoice INV-001",
        "from": {"emailAddress": {"address": "provider@example.com"}},
        "receivedDateTime": "2024-07-01T09:00:00Z",
        "attachments": [
            {
                "id": "att-001",
                "name": "invoice.pdf",
                "contentType": "application/pdf",
            }
        ],
    }

    with (
        patch(
            "app.services.invoice_ingestion_service.GraphClient"
        ) as MockGraph,
        patch(
            "app.services.invoice_ingestion_service.GCSClient"
        ) as MockGCS,
        patch(
            "app.services.invoice_ingestion_service.get_ocr_client"
        ) as MockGetOcrClient,
    ):
        mock_graph = AsyncMock()
        mock_graph.download_attachment.return_value = b"%PDF-fake"
        mock_graph.mark_message_as_read.return_value = None
        mock_graph.move_message_to_folder.return_value = None
        MockGraph.return_value = mock_graph

        mock_gcs = AsyncMock()
        mock_gcs.upload_pdf.return_value = "gs://bucket/invoices/invoice.pdf"
        mock_gcs.upload_json.return_value = "gs://bucket/invoices/ocr/invoice_ocr.json"
        MockGCS.return_value = mock_gcs

        mock_docai = AsyncMock()
        mock_docai.parse_invoice.return_value = fake_parse_result
        MockGetOcrClient.return_value = mock_docai

        invoice = await process_invoice_email(db_session, fake_message)

    assert invoice.id is not None
    assert invoice.invoice_number == "INV-001"
    assert invoice.total_amount == Decimal("550.00")
    assert invoice.gcs_pdf_path == "gs://bucket/invoices/invoice.pdf"
    assert invoice.gcs_json_path == "gs://bucket/invoices/ocr/invoice_ocr.json"
    assert invoice.status == "pending"

    # Verify line items
    from sqlalchemy import select

    li_result = await db_session.execute(
        select(InvoiceLineItem).where(InvoiceLineItem.invoice_id == invoice.id)
    )
    line_items = li_result.scalars().all()
    assert len(line_items) == 1
    assert line_items[0].description == "Daily activities"


# ---------------------------------------------------------------------------
# 5. test_process_invoice_email_logs_audit
# ---------------------------------------------------------------------------


async def test_process_invoice_email_logs_audit(db_session):
    """process_invoice_email writes an audit log entry."""
    from sqlalchemy import select

    from app.models.audit_log import AuditLog
    from app.services.invoice_ingestion_service import process_invoice_email

    fake_parse_result = InvoiceParseResult(
        supplier_name="Audit Provider",
        supplier_abn=None,
        invoice_number="AUDIT-001",
        invoice_date=date(2024, 8, 1),
        total_amount=Decimal("200.00"),
        gst_amount=Decimal("20.00"),
        line_items=[],
        confidence_score=0.90,
        raw_response={},
    )

    fake_message = {
        "id": "msg-audit-456",
        "conversationId": "conv-audit-456",
        "subject": "Invoice AUDIT-001",
        "from": {"emailAddress": {"address": "audit@example.com"}},
        "receivedDateTime": "2024-08-01T10:00:00Z",
        "attachments": [
            {"id": "att-002", "name": "audit.pdf", "contentType": "application/pdf"}
        ],
    }

    with (
        patch("app.services.invoice_ingestion_service.GraphClient") as MockGraph,
        patch("app.services.invoice_ingestion_service.GCSClient") as MockGCS,
        patch("app.services.invoice_ingestion_service.get_ocr_client") as MockGetOcrClient,
    ):
        mock_graph = AsyncMock()
        mock_graph.download_attachment.return_value = b"%PDF-audit"
        mock_graph.mark_message_as_read.return_value = None
        mock_graph.move_message_to_folder.return_value = None
        MockGraph.return_value = mock_graph

        mock_gcs = AsyncMock()
        mock_gcs.upload_pdf.return_value = "gs://bucket/audit.pdf"
        mock_gcs.upload_json.return_value = "gs://bucket/audit_ocr.json"
        MockGCS.return_value = mock_gcs

        mock_docai = AsyncMock()
        mock_docai.parse_invoice.return_value = fake_parse_result
        MockGetOcrClient.return_value = mock_docai

        invoice = await process_invoice_email(db_session, fake_message)

    audit_result = await db_session.execute(
        select(AuditLog).where(AuditLog.entity_id == invoice.id)
    )
    audit_entries = audit_result.scalars().all()
    assert len(audit_entries) >= 1
    entry = audit_entries[0]
    assert entry.action == "invoice_ingested"
    assert entry.entity_type == "Invoice"


# ---------------------------------------------------------------------------
# 6. test_list_invoices_filter_by_status
# ---------------------------------------------------------------------------


async def test_list_invoices_filter_by_status(test_client):
    """GET /invoices/?invoice_status=pending returns only pending invoices."""
    from sqlalchemy import select

    from app.db import get_db

    # Create invoices directly in the DB via the test session
    # We need a separate DB session that the test_client also sees, so use the
    # session injected by test_client via dependency override.
    resp = await test_client.get("/api/v1/invoices/?invoice_status=pending")
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    for item in body["items"]:
        assert item["status"] == "pending"


# ---------------------------------------------------------------------------
# 7. test_get_invoice_with_line_items
# ---------------------------------------------------------------------------


async def test_get_invoice_with_line_items(db_session, test_client):
    """GET /invoices/{id} returns the invoice with nested line items."""
    # Insert an invoice directly
    invoice = Invoice(
        invoice_number="TEST-GET-001",
        invoice_date=date(2024, 9, 1),
        total_amount=Decimal("300.00"),
        gst_amount=Decimal("30.00"),
        gcs_pdf_path="gs://bucket/test.pdf",
        status="pending",
    )
    db_session.add(invoice)
    await db_session.flush()

    line_item = InvoiceLineItem(
        invoice_id=invoice.id,
        description="Community access",
        quantity=Decimal("3"),
        unit_price=Decimal("100.00"),
        total=Decimal("300.00"),
    )
    db_session.add(line_item)
    await db_session.commit()
    await db_session.refresh(invoice)

    resp = await test_client.get(f"/api/v1/invoices/{invoice.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(invoice.id)
    assert body["invoice_number"] == "TEST-GET-001"
    assert isinstance(body["line_items"], list)
    assert len(body["line_items"]) == 1
    assert body["line_items"][0]["description"] == "Community access"
