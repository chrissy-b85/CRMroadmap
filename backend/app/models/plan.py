"""ORM model for Plan."""
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    participant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("participants.id"), nullable=False, index=True
    )
    plan_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    plan_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_funding: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    plan_manager: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    participant: Mapped["Participant"] = relationship(  # type: ignore[name-defined]
        "Participant", back_populates="plans"
    )
    support_categories = relationship("SupportCategory", back_populates="plan")
    invoices = relationship("Invoice", back_populates="plan")
