"""Amazon Textract invoice OCR client."""
from __future__ import annotations

import asyncio
import os

from app.integrations.document_ai.parser import (
    InvoiceLineItemParsed,
    InvoiceParseResult,
    _to_date,
    _to_decimal,
)


class TextractClient:
    """Async wrapper around the AWS Textract AnalyzeExpense API."""

    def __init__(self) -> None:
        self._region: str = os.getenv("AWS_REGION", "ap-southeast-2")
        self._access_key_id: str | None = os.getenv("AWS_ACCESS_KEY_ID")
        self._secret_access_key: str | None = os.getenv("AWS_SECRET_ACCESS_KEY")

    def _call_textract(self, pdf_bytes: bytes) -> dict:
        """Call AWS Textract AnalyzeExpense synchronously. Separated for testability."""
        import boto3

        client = boto3.client(
            "textract",
            region_name=self._region,
            aws_access_key_id=self._access_key_id,
            aws_secret_access_key=self._secret_access_key,
        )
        response = client.analyze_expense(Document={"Bytes": pdf_bytes})
        return response

    async def parse_invoice(self, pdf_bytes: bytes) -> InvoiceParseResult:
        """Send *pdf_bytes* to Textract and return a structured parse result."""
        loop = asyncio.get_event_loop()
        raw = await loop.run_in_executor(None, lambda: self._call_textract(pdf_bytes))
        return self._parse_response(raw)

    def _parse_response(self, raw: dict) -> InvoiceParseResult:
        """Convert a raw Textract AnalyzeExpense response into an InvoiceParseResult."""
        result = InvoiceParseResult(raw_response=raw)

        expense_documents: list[dict] = raw.get("ExpenseDocuments", [])
        if not expense_documents:
            return result

        # Use the first expense document
        doc = expense_documents[0]

        # --- SummaryFields ---
        summary_fields: list[dict] = doc.get("SummaryFields", [])
        field_map: dict[str, str] = {}
        confidence_values: list[float] = []

        for field in summary_fields:
            field_type = (field.get("Type") or {}).get("Text", "")
            value_detection = field.get("ValueDetection") or {}
            text = value_detection.get("Text")
            confidence = value_detection.get("Confidence")
            if field_type and text:
                field_map[field_type] = text
            if confidence is not None:
                confidence_values.append(float(confidence))

        result.supplier_name = field_map.get("VENDOR_NAME")
        result.supplier_abn = field_map.get(
            "VENDOR_TAX_REGISTRATION_NUMBER"
        ) or field_map.get("TAX_PAYER_ID")
        result.invoice_number = field_map.get("INVOICE_RECEIPT_ID")
        result.invoice_date = _to_date(field_map.get("INVOICE_RECEIPT_DATE"))
        result.due_date = _to_date(field_map.get("DUE_DATE"))
        result.total_amount = _to_decimal(
            field_map.get("AMOUNT_DUE") or field_map.get("TOTAL")
        )
        result.gst_amount = _to_decimal(field_map.get("TAX"))

        if confidence_values:
            result.confidence_score = sum(confidence_values) / len(confidence_values)

        # --- LineItemGroups ---
        line_items: list[InvoiceLineItemParsed] = []
        for group in doc.get("LineItemGroups", []):
            for line_item in group.get("LineItems", []):
                item = InvoiceLineItemParsed()
                for expense_field in line_item.get("LineItemExpenseFields", []):
                    field_type = (expense_field.get("Type") or {}).get("Text", "")
                    value_detection = expense_field.get("ValueDetection") or {}
                    text = value_detection.get("Text")
                    if field_type == "ITEM":
                        item.description = text
                    elif field_type == "QUANTITY":
                        item.quantity = _to_decimal(text)
                    elif field_type == "UNIT_PRICE":
                        item.unit_price = _to_decimal(text)
                    elif field_type in ("EXPENSE_ROW", "PRICE"):
                        item.total = _to_decimal(text)
                line_items.append(item)

        result.line_items = line_items
        return result
