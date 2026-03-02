from sqlalchemy import Boolean, Column, Date, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, UUIDMixin


class Plan(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "plans"

    participant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("participants.id"),
        nullable=False,
        index=True,
    )
    plan_start_date = Column(Date, nullable=False)
    plan_end_date = Column(Date, nullable=False)
    total_funding = Column(Numeric(12, 2), nullable=False)
    plan_manager = Column(String(255))
    is_active = Column(Boolean, default=True)

    participant = relationship("Participant", back_populates="plans")
    support_categories = relationship("SupportCategory", back_populates="plan")
    invoices = relationship("Invoice", back_populates="plan")
