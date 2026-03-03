"""SupportCategory ORM model."""

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class SupportCategory(Base):
    __tablename__ = "support_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False, index=True
    )
    ndis_support_category: Mapped[str] = mapped_column(String(200), nullable=False)
    ndis_support_number: Mapped[str | None] = mapped_column(String(10), nullable=True)
    budget_allocated: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    budget_spent: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )

    plan: Mapped["Plan"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Plan", back_populates="support_categories"
    )
    invoice_line_items = relationship(
        "InvoiceLineItem", back_populates="support_category"
    )

    @property
    def budget_remaining(self) -> Decimal:
        """Computed remaining budget."""
        return self.budget_allocated - self.budget_spent

    @property
    def utilisation_percent(self) -> float:
        """Computed utilisation as a percentage."""
        if not self.budget_allocated:
            return 0.0
        return float(self.budget_spent / self.budget_allocated * 100)

    @property
    def is_overspent(self) -> bool:
        """True when budget_spent exceeds budget_allocated."""
        return self.budget_spent > self.budget_allocated
