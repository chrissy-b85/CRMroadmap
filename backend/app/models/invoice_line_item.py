from sqlalchemy import Column, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import TimestampMixin, UUIDMixin


class InvoiceLineItem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "invoice_line_items"

    invoice_id = Column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id"),
        nullable=False,
        index=True,
    )
    support_item_number = Column(String(50))
    description = Column(Text)
    unit_price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    total = Column(Numeric(12, 2), nullable=False)
    support_category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("support_categories.id"),
        index=True,
    )

    invoice = relationship("Invoice", back_populates="line_items")
    support_category = relationship(
        "SupportCategory", back_populates="invoice_line_items"
    )
