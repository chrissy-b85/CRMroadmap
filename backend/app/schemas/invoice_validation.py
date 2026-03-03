"""Pydantic v2 schemas for invoice validation report endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ValidationResultOut(BaseModel):
    rule_name: str
    passed: bool
    message: str
    severity: str


class ValidationReportOut(BaseModel):
    invoice_id: UUID
    passed: bool
    final_status: str
    results: list[ValidationResultOut]
    validated_at: datetime
