"""Parse Google Document AI Invoice Parser response into structured data."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation


@dataclass
class InvoiceLineItemParsed:
    description: str | None = None
    quantity: Decimal | None = None
    unit_price: Decimal | None = None
    total: Decimal | None = None
    support_item_number: str | None = None


@dataclass
class InvoiceParseResult:
    supplier_name: str | None = None
    supplier_abn: str | None = None
    invoice_number: str | None = None
    invoice_date: date | None = None
    due_date: date | None = None
    total_amount: Decimal | None = None
    gst_amount: Decimal | None = None
    line_items: list[InvoiceLineItemParsed] = field(default_factory=list)
    confidence_score: float = 0.0
    raw_response: dict = field(default_factory=dict)


def _get_field_value(entity: dict, field_name: str) -> str | None:
    """Extract a text value from a Document AI entity dict by type."""
    if entity.get("type_") == field_name or entity.get("type") == field_name:
        return entity.get("mentionText") or entity.get("mention_text")
    return None


def _to_decimal(value: str | None) -> Decimal | None:
    """Safely convert a string to Decimal, stripping currency symbols."""
    if not value:
        return None
    cleaned = value.replace("$", "").replace(",", "").strip()
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _to_date(value: str | None) -> date | None:
    """Safely parse an ISO or common date string."""
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            from datetime import datetime

            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def parse_document_ai_response(response: dict) -> InvoiceParseResult:
    """Convert a raw Document AI API response dict into an InvoiceParseResult.

    The response dict is expected to follow the structure returned by the
    Google Cloud Document AI Invoice Parser (REST or Python SDK v2 format).
    """
    result = InvoiceParseResult(raw_response=response)

    document = response.get("document", response)
    entities: list[dict] = document.get("entities", [])

    field_map: dict[str, str] = {}
    for entity in entities:
        etype = entity.get("type_") or entity.get("type", "")
        text = entity.get("mentionText") or entity.get("mention_text", "")
        if etype and text:
            field_map[etype] = text

        # Collect confidence scores for an average
        if "confidence" in entity:
            # Use the first entity confidence as a rough overall score
            if result.confidence_score == 0.0:
                result.confidence_score = float(entity["confidence"])

    result.supplier_name = field_map.get("supplier_name")
    result.supplier_abn = field_map.get("supplier_tax_id") or field_map.get("supplier_abn")
    result.invoice_number = field_map.get("invoice_id")
    result.invoice_date = _to_date(field_map.get("invoice_date"))
    result.due_date = _to_date(field_map.get("due_date"))
    result.total_amount = _to_decimal(field_map.get("total_amount"))
    result.gst_amount = _to_decimal(field_map.get("total_tax_amount")) or _to_decimal(
        field_map.get("net_amount")
    )

    # Line items are represented as child entities
    line_items: list[InvoiceLineItemParsed] = []
    for entity in entities:
        etype = entity.get("type_") or entity.get("type", "")
        if etype == "line_item":
            item = InvoiceLineItemParsed()
            for prop in entity.get("properties", []):
                ptype = prop.get("type_") or prop.get("type", "")
                ptext = prop.get("mentionText") or prop.get("mention_text", "")
                if ptype == "line_item/description":
                    item.description = ptext
                elif ptype == "line_item/quantity":
                    item.quantity = _to_decimal(ptext)
                elif ptype == "line_item/unit_price":
                    item.unit_price = _to_decimal(ptext)
                elif ptype == "line_item/amount":
                    item.total = _to_decimal(ptext)
                elif ptype == "line_item/product_code":
                    item.support_item_number = ptext
            line_items.append(item)

    result.line_items = line_items
    return result
