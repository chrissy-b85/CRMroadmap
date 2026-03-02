from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    auth0_id = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    role = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True))

    reviewed_invoices = relationship(
        "Invoice", back_populates="reviewer", foreign_keys="Invoice.reviewed_by"
    )
    uploaded_documents = relationship(
        "Document", back_populates="uploader", foreign_keys="Document.uploaded_by"
    )
    audit_logs = relationship("AuditLog", back_populates="user")
