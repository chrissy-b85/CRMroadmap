from sqlalchemy import Column, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, UUIDMixin


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
    budget_remaining = Column(Numeric(12, 2))

    plan = relationship("Plan", back_populates="support_categories")
    invoice_line_items = relationship(
        "InvoiceLineItem", back_populates="support_category"
    )
