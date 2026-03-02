from sqlalchemy import Boolean, Column, Date, String, Text
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, UUIDMixin


class Participant(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "participants"

    ndis_number = Column(String(20), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date)
    email = Column(String(255))
    phone = Column(String(20))
    address = Column(Text)
    is_active = Column(Boolean, default=True)

    plans = relationship("Plan", back_populates="participant")
    documents = relationship("Document", back_populates="participant")
    invoices = relationship("Invoice", back_populates="participant")
