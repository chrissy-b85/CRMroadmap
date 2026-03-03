from sqlalchemy import Column, Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import TimestampMixin, UUIDMixin


class Invoice(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "invoices"

    participant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("participants.id"),
        nullable=True,
        index=True,
    )
    provider_id = Column(
        UUID(as_uuid=True),
        ForeignKey("providers.id"),
        nullable=True,
        index=True,
    )
    plan_id = Column(
        UUID(as_uuid=True),
        ForeignKey("plans.id"),
        nullable=True,
        index=True,
    )
    invoice_number = Column(String(100), nullable=True)
    gcs_pdf_path = Column(String(500), nullable=True)
    gcs_json_path = Column(String(500))
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date)
    total_amount = Column(Numeric(12, 2), nullable=False)
    gst_amount = Column(Numeric(12, 2), default=0)
    status = Column(String(50), default="pending")
    ocr_confidence = Column(Numeric(5, 2))
    xero_invoice_id = Column(String(100))
    email_thread_id = Column(
        UUID(as_uuid=True),
        ForeignKey("email_threads.id"),
        index=True,
    )
    reviewed_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
    )
    reviewed_at = Column(DateTime(timezone=True))

    participant = relationship("Participant", back_populates="invoices")
    provider = relationship("Provider", back_populates="invoices")
    plan = relationship("Plan", back_populates="invoices")
    email_thread = relationship("EmailThread", back_populates="invoices")
    reviewer = relationship(
        "User", back_populates="reviewed_invoices", foreign_keys=[reviewed_by]
    )
    line_items = relationship("InvoiceLineItem", back_populates="invoice")
    documents = relationship("Document", back_populates="invoice")
