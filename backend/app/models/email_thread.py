from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import TimestampMixin, UUIDMixin


class EmailThread(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "email_threads"

    graph_message_id = Column(String(255), unique=True, nullable=False)
    graph_thread_id = Column(String(255), nullable=True)
    subject = Column(String(500))
    sender_email = Column(String(255))
    sender_name = Column(String(255), nullable=True)
    received_at = Column(DateTime(timezone=True))
    direction = Column(String(20), default="inbound")  # 'inbound' | 'outbound'
    body_preview = Column(String(1000), nullable=True)
    has_attachments = Column(Boolean, default=False)
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
    invoice_id = Column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id"),
        nullable=True,
        index=True,
    )

    participant = relationship("Participant", back_populates="email_threads")
    provider = relationship("Provider", back_populates="email_threads")
    invoices = relationship("Invoice", back_populates="email_thread", foreign_keys=[invoice_id])
