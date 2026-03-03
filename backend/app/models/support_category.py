from decimal import Decimal

from sqlalchemy import Column, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import TimestampMixin, UUIDMixin


class SupportCategory(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "support_categories"

    plan_id = Column(
        UUID(as_uuid=True),
        ForeignKey("plans.id"),
        nullable=False,
        index=True,
    )
    ndis_support_category = Column(String(100), nullable=False)
    budget_allocated = Column(Numeric(12, 2), nullable=False)
    budget_spent = Column(Numeric(12, 2), default=0)

    plan = relationship("Plan", back_populates="support_categories")
    invoice_line_items = relationship(
        "InvoiceLineItem", back_populates="support_category"
    )

    @hybrid_property
    def budget_remaining(self) -> Decimal:
        """Computed remaining budget."""
        spent = self.budget_spent or Decimal("0.00")
        return (self.budget_allocated or Decimal("0.00")) - spent
"""SupportCategory ORM model (defined in participant.py, re-exported here)."""
from app.models.participant import SupportCategory  # noqa: F401
