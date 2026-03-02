from sqlalchemy import Boolean, Column, String, Text
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, UUIDMixin


class Provider(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "providers"

    abn = Column(String(11), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(20))
    address = Column(Text)
    bank_bsb = Column(String(6))
    bank_account = Column(String(20))
    xero_contact_id = Column(String(100))
    is_active = Column(Boolean, default=True)

    invoices = relationship("Invoice", back_populates="provider")
    email_threads = relationship("EmailThread", back_populates="provider")
