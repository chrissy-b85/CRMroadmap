from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import TimestampMixin, UUIDMixin


class Document(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "documents"

    participant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("participants.id"),
        index=True,
    )
    invoice_id = Column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id"),
        index=True,
    )
    document_type = Column(String(50), nullable=False)
    gcs_bucket = Column(String(255), nullable=False)
    gcs_path = Column(String(500), nullable=False)
    original_filename = Column(String(255))
    mime_type = Column(String(100))
    file_size_bytes = Column(Integer)
    uploaded_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
    )

    participant = relationship("Participant", back_populates="documents")
    invoice = relationship("Invoice", back_populates="documents")
    uploader = relationship(
        "User", back_populates="uploaded_documents", foreign_keys=[uploaded_by]
    )
