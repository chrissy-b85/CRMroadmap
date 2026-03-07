"""Tests for the Amazon Textract OCR client."""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.integrations.textract.client import TextractClient


FAKE_TEXTRACT_RESPONSE = {
    "ExpenseDocuments": [
        {
            "SummaryFields": [
                {
                    "Type": {"Text": "VENDOR_NAME"},
                    "ValueDetection": {"Text": "NDIS Provider Pty Ltd", "Confidence": 99.0},
                },
                {
                    "Type": {"Text": "VENDOR_TAX_REGISTRATION_NUMBER"},
                    "ValueDetection": {"Text": "12 345 678 901", "Confidence": 98.0},
                },
                {
                    "Type": {"Text": "INVOICE_RECEIPT_ID"},
                    "ValueDetection": {"Text": "INV-2024-001", "Confidence": 99.0},
                },
                {
                    "Type": {"Text": "INVOICE_RECEIPT_DATE"},
                    "ValueDetection": {"Text": "2024-08-01", "Confidence": 97.0},
                },
                {
                    "Type": {"Text": "AMOUNT_DUE"},
                    "ValueDetection": {"Text": "$550.00", "Confidence": 99.0},
                },
                {
                    "Type": {"Text": "TAX"},
                    "ValueDetection": {"Text": "$50.00", "Confidence": 99.0},
                },
            ],
            "LineItemGroups": [
                {
                    "LineItems": [
                        {
                            "LineItemExpenseFields": [
                                {
                                    "Type": {"Text": "ITEM"},
                                    "ValueDetection": {"Text": "Daily activities support", "Confidence": 95.0},
                                },
                                {
                                    "Type": {"Text": "QUANTITY"},
                                    "ValueDetection": {"Text": "2", "Confidence": 95.0},
                                },
                                {
                                    "Type": {"Text": "UNIT_PRICE"},
                                    "ValueDetection": {"Text": "$250.00", "Confidence": 95.0},
                                },
                                {
                                    "Type": {"Text": "PRICE"},
                                    "ValueDetection": {"Text": "$500.00", "Confidence": 95.0},
                                },
                            ]
                        }
                    ]
                }
            ],
        }
    ]
}


@pytest.mark.asyncio
async def test_textract_client_parses_invoice():
    """TextractClient.parse_invoice returns a correctly populated InvoiceParseResult."""
    client = TextractClient()

    with patch.object(client, "_call_textract", return_value=FAKE_TEXTRACT_RESPONSE):
        result = await client.parse_invoice(b"%PDF-fake")

    assert result.supplier_name == "NDIS Provider Pty Ltd"
    assert result.supplier_abn == "12 345 678 901"
    assert result.invoice_number == "INV-2024-001"
    assert result.total_amount == Decimal("550.00")
    assert result.gst_amount == Decimal("50.00")
    assert len(result.line_items) == 1
    assert result.line_items[0].description == "Daily activities support"
    assert result.line_items[0].quantity == Decimal("2")
    assert result.line_items[0].unit_price == Decimal("250.00")
    assert result.confidence_score > 0


@pytest.mark.asyncio
async def test_textract_client_empty_response():
    """TextractClient.parse_invoice handles an empty Textract response gracefully."""
    client = TextractClient()
    empty_response = {"ExpenseDocuments": []}

    with patch.object(client, "_call_textract", return_value=empty_response):
        result = await client.parse_invoice(b"%PDF-empty")

    assert result.supplier_name is None
    assert result.total_amount is None
    assert result.line_items == []


def test_ocr_factory_returns_documentai_by_default(monkeypatch):
    """get_ocr_client() returns DocumentAIClient when OCR_BACKEND is not set."""
    monkeypatch.delenv("OCR_BACKEND", raising=False)
    from app.integrations.ocr import get_ocr_client
    from app.integrations.document_ai.client import DocumentAIClient
    client = get_ocr_client()
    assert isinstance(client, DocumentAIClient)


def test_ocr_factory_returns_textract(monkeypatch):
    """get_ocr_client() returns TextractClient when OCR_BACKEND=textract."""
    monkeypatch.setenv("OCR_BACKEND", "textract")
    from app.integrations.ocr import get_ocr_client
    from app.integrations.textract.client import TextractClient
    # Reload to pick up env change
    import importlib
    import app.integrations.ocr as ocr_module
    importlib.reload(ocr_module)
    client = ocr_module.get_ocr_client()
    assert isinstance(client, TextractClient)
