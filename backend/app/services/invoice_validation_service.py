"""Invoice validation service.

Implements a composable rules engine for NDIS invoice compliance checks.
Each rule returns a ValidationResult; the aggregate report drives the invoice
status transition.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit_log import AuditLog
from app.models.invoice import Invoice
from app.models.participant import Plan, SupportCategory
from app.models.provider import Provider

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load NDIS price guide fixture once at module import time.
# TODO: Replace with live NDIS Price Guide API call when available.
# ---------------------------------------------------------------------------
_PRICE_GUIDE_PATH = Path(__file__).parent.parent / "data" / "ndis_price_guide.json"

try:
    with _PRICE_GUIDE_PATH.open() as _f:
        NDIS_PRICE_GUIDE: dict[str, dict] = json.load(_f)
except FileNotFoundError:
    logger.warning("NDIS price guide fixture not found at %s", _PRICE_GUIDE_PATH)
    NDIS_PRICE_GUIDE = {}

OCR_CONFIDENCE_THRESHOLD = Decimal("0.85")
GST_TOLERANCE = Decimal("0.10")


# ---------------------------------------------------------------------------
# Result data classes
# ---------------------------------------------------------------------------


@dataclass
class ValidationResult:
    rule_name: str
    passed: bool
    message: str
    severity: str  # "error" | "warning"


@dataclass
class InvoiceValidationReport:
    invoice_id: UUID
    passed: bool
    results: list[ValidationResult] = field(default_factory=list)
    final_status: str = "PENDING_APPROVAL"


# ---------------------------------------------------------------------------
# Individual validation rules
# ---------------------------------------------------------------------------


async def validate_provider_abn(db: AsyncSession, invoice: Invoice) -> ValidationResult:
    """Check invoice ABN matches a known active provider in DB."""
    if invoice.provider_id is None:
        return ValidationResult(
            rule_name="validate_provider_abn",
            passed=False,
            message="No provider matched for this invoice — ABN not found in database.",
            severity="error",
        )
    result = await db.execute(
        select(Provider).where(
            Provider.id == invoice.provider_id,
            Provider.is_active.is_(True),
        )
    )
    provider = result.scalar_one_or_none()
    if provider is None:
        return ValidationResult(
            rule_name="validate_provider_abn",
            passed=False,
            message="Provider is inactive or not found in the database.",
            severity="error",
        )
    return ValidationResult(
        rule_name="validate_provider_abn",
        passed=True,
        message=f"Provider ABN matched: {provider.abn}.",
        severity="error",
    )


async def validate_ndis_support_items(
    db: AsyncSession, invoice: Invoice  # noqa: ARG001
) -> ValidationResult:
    """Check each line item support_item_number exists in the NDIS Support Catalogue."""
    unknown = []
    for item in invoice.line_items:
        num = item.support_item_number
        if num and num not in NDIS_PRICE_GUIDE:
            unknown.append(num)
    if unknown:
        return ValidationResult(
            rule_name="validate_ndis_support_items",
            passed=False,
            message=f"Unknown NDIS support item numbers: {', '.join(unknown)}.",
            severity="error",
        )
    return ValidationResult(
        rule_name="validate_ndis_support_items",
        passed=True,
        message="All support item numbers are valid.",
        severity="error",
    )


async def validate_unit_prices(
    db: AsyncSession, invoice: Invoice  # noqa: ARG001
) -> ValidationResult:
    """Check each line item unit price does not exceed NDIS price guide maxima."""
    violations = []
    for item in invoice.line_items:
        if not item.support_item_number:
            continue
        guide_entry = NDIS_PRICE_GUIDE.get(item.support_item_number)
        if guide_entry is None:
            continue
        max_price = Decimal(str(guide_entry["price_limit_national"]))
        if item.unit_price > max_price:
            violations.append(
                f"{item.support_item_number}: ${item.unit_price} > max ${max_price}"
            )
    if violations:
        return ValidationResult(
            rule_name="validate_unit_prices",
            passed=False,
            message=f"Unit price exceeds NDIS limit: {'; '.join(violations)}.",
            severity="error",
        )
    return ValidationResult(
        rule_name="validate_unit_prices",
        passed=True,
        message="All unit prices are within NDIS limits.",
        severity="error",
    )


async def validate_budget_availability(
    db: AsyncSession, invoice: Invoice
) -> ValidationResult:
    """Check participant has sufficient budget in the relevant support category."""
    if not invoice.line_items:
        return ValidationResult(
            rule_name="validate_budget_availability",
            passed=True,
            message="No line items to check budget against.",
            severity="error",
        )

    # Group line items by support_category_id and sum totals
    category_totals: dict[UUID, Decimal] = {}
    for item in invoice.line_items:
        if item.support_category_id:
            cat_id = item.support_category_id
            category_totals[cat_id] = category_totals.get(cat_id, Decimal("0")) + (
                item.total or Decimal("0")
            )

    if not category_totals:
        return ValidationResult(
            rule_name="validate_budget_availability",
            passed=True,
            message="No support categories assigned to line items; skipping.",
            severity="error",
        )

    insufficient = []
    for cat_id, required in category_totals.items():
        result = await db.execute(
            select(SupportCategory).where(SupportCategory.id == cat_id)
        )
        cat = result.scalar_one_or_none()
        if cat is None:
            continue
        remaining = cat.budget_remaining
        if required > remaining:
            insufficient.append(
                f"{cat.ndis_support_category}: requires ${required}, "
                f"only ${remaining} remaining"
            )

    if insufficient:
        return ValidationResult(
            rule_name="validate_budget_availability",
            passed=False,
            message=f"Insufficient budget: {'; '.join(insufficient)}.",
            severity="error",
        )
    return ValidationResult(
        rule_name="validate_budget_availability",
        passed=True,
        message="Sufficient budget available for all support categories.",
        severity="error",
    )


async def validate_active_plan(db: AsyncSession, invoice: Invoice) -> ValidationResult:
    """Check invoice date falls within an active participant plan period."""
    if invoice.plan_id is None:
        return ValidationResult(
            rule_name="validate_active_plan",
            passed=False,
            message="No plan linked to this invoice.",
            severity="error",
        )
    result = await db.execute(
        select(Plan).where(Plan.id == invoice.plan_id, Plan.is_active.is_(True))
    )
    plan = result.scalar_one_or_none()
    if plan is None:
        return ValidationResult(
            rule_name="validate_active_plan",
            passed=False,
            message="No active plan found for this invoice.",
            severity="error",
        )
    invoice_date = invoice.invoice_date
    if not (plan.plan_start_date <= invoice_date <= plan.plan_end_date):
        return ValidationResult(
            rule_name="validate_active_plan",
            passed=False,
            message=(
                f"Invoice date {invoice_date} is outside the active plan period "
                f"({plan.plan_start_date} – {plan.plan_end_date})."
            ),
            severity="error",
        )
    return ValidationResult(
        rule_name="validate_active_plan",
        passed=True,
        message="Invoice date falls within the active plan period.",
        severity="error",
    )


async def validate_not_duplicate(
    db: AsyncSession, invoice: Invoice
) -> ValidationResult:
    """Check no existing invoice with same provider + invoice_number combination."""
    if not invoice.provider_id or not invoice.invoice_number:
        return ValidationResult(
            rule_name="validate_not_duplicate",
            passed=True,
            message="Cannot check duplicates without provider and invoice number.",
            severity="error",
        )
    result = await db.execute(
        select(Invoice).where(
            Invoice.provider_id == invoice.provider_id,
            Invoice.invoice_number == invoice.invoice_number,
            Invoice.id != invoice.id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        return ValidationResult(
            rule_name="validate_not_duplicate",
            passed=False,
            message=(
                f"Duplicate invoice detected: "
                f"invoice number '{invoice.invoice_number}' "
                f"already exists for this provider (id={existing.id})."
            ),
            severity="error",
        )
    return ValidationResult(
        rule_name="validate_not_duplicate",
        passed=True,
        message="No duplicate invoice found.",
        severity="error",
    )


async def validate_ocr_confidence(
    db: AsyncSession, invoice: Invoice  # noqa: ARG001
) -> ValidationResult:
    """Flag if Document AI confidence score < 0.85 (warning, not error)."""
    if invoice.ocr_confidence is None:
        return ValidationResult(
            rule_name="validate_ocr_confidence",
            passed=True,
            message="OCR confidence score not available.",
            severity="warning",
        )
    confidence = Decimal(str(invoice.ocr_confidence))
    if confidence < OCR_CONFIDENCE_THRESHOLD:
        return ValidationResult(
            rule_name="validate_ocr_confidence",
            passed=False,
            message=(
                f"OCR confidence score {confidence} is below the threshold "
                f"of {OCR_CONFIDENCE_THRESHOLD}. Manual review recommended."
            ),
            severity="warning",
        )
    return ValidationResult(
        rule_name="validate_ocr_confidence",
        passed=True,
        message=f"OCR confidence score {confidence} is acceptable.",
        severity="warning",
    )


async def validate_gst_calculation(
    db: AsyncSession, invoice: Invoice  # noqa: ARG001
) -> ValidationResult:
    """Check GST amount = total × 10/110 (within $0.10 tolerance)."""
    if invoice.gst_amount is None or invoice.total_amount is None:
        return ValidationResult(
            rule_name="validate_gst_calculation",
            passed=True,
            message="Cannot verify GST — amounts not set.",
            severity="error",
        )
    expected_gst = Decimal(str(invoice.total_amount)) * Decimal("10") / Decimal("110")
    actual_gst = Decimal(str(invoice.gst_amount))
    diff = abs(actual_gst - expected_gst)
    if diff > GST_TOLERANCE:
        return ValidationResult(
            rule_name="validate_gst_calculation",
            passed=False,
            message=(
                f"GST amount ${actual_gst} does not match expected "
                f"${expected_gst:.2f} (difference ${diff:.2f} exceeds tolerance "
                f"${GST_TOLERANCE})."
            ),
            severity="error",
        )
    return ValidationResult(
        rule_name="validate_gst_calculation",
        passed=True,
        message=f"GST amount ${actual_gst} is correct (expected ~${expected_gst:.2f}).",
        severity="error",
    )


# ---------------------------------------------------------------------------
# Main validation orchestrator
# ---------------------------------------------------------------------------

_ALL_RULES = [
    validate_provider_abn,
    validate_ndis_support_items,
    validate_unit_prices,
    validate_budget_availability,
    validate_active_plan,
    validate_not_duplicate,
    validate_ocr_confidence,
    validate_gst_calculation,
]


async def validate_invoice(
    db: AsyncSession, invoice_id: UUID
) -> InvoiceValidationReport:
    """Run all validation rules against an invoice.

    - If any errors → set status to FLAGGED, store validation_results JSON
    - If only warnings → set status to PENDING_APPROVAL with warning flags
    - If all pass → set status to PENDING_APPROVAL
    - Write audit log entry with full report
    """
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.line_items))
        .where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if invoice is None:
        raise ValueError(f"Invoice {invoice_id} not found")

    results: list[ValidationResult] = []
    for rule_fn in _ALL_RULES:
        try:
            rule_result = await rule_fn(db, invoice)
        except Exception:  # noqa: BLE001
            logger.exception("Rule %s raised an exception", rule_fn.__name__)
            rule_result = ValidationResult(
                rule_name=rule_fn.__name__,
                passed=False,
                message="Rule execution failed unexpectedly.",
                severity="error",
            )
        results.append(rule_result)

    has_errors = any(r.severity == "error" and not r.passed for r in results)
    final_status = "FLAGGED" if has_errors else "PENDING_APPROVAL"
    passed = not has_errors

    # Persist results onto invoice
    invoice.status = final_status
    invoice.validation_results = [
        {
            "rule_name": r.rule_name,
            "passed": r.passed,
            "message": r.message,
            "severity": r.severity,
        }
        for r in results
    ]

    validated_at = datetime.now(tz=timezone.utc)

    audit = AuditLog(
        action="invoice_validated",
        entity_type="Invoice",
        entity_id=invoice.id,
        new_values={
            "final_status": final_status,
            "passed": passed,
            "validated_at": validated_at.isoformat(),
            "results": invoice.validation_results,
        },
    )
    db.add(audit)
    await db.commit()
    await db.refresh(invoice)

    report = InvoiceValidationReport(
        invoice_id=invoice_id,
        passed=passed,
        results=results,
        final_status=final_status,
    )
    return report
