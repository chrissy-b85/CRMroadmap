from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import TimestampMixin, UUIDMixin


class EmailThread(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "email_threads"

    outlook_thread_id = Column(String(255), unique=True, nullable=False)
    outlook_message_id = Column(String(255))
    subject = Column(String(500))
    sender_email = Column(String(255))
    received_at = Column(DateTime(timezone=True))
    processed = Column(Boolean, default=False)
    provider_id = Column(
        UUID(as_uuid=True),
        ForeignKey("providers.id"),
        index=True,
    )

    provider = relationship("Provider", back_populates="email_threads")
    invoices = relationship("Invoice", back_populates="email_thread")
