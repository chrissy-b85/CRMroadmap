"""ORM models for Participant (and re-exports Plan for backwards compat)."""
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ndis_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
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

    plans: Mapped[list["Plan"]] = relationship(  # type: ignore[name-defined]
        "Plan", back_populates="participant", cascade="all, delete-orphan"
    )
    documents = relationship("Document", back_populates="participant")
    invoices = relationship("Invoice", back_populates="participant")


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    participant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("participants.id"), nullable=False
    )
    plan_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    plan_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_funding: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
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

    participant: Mapped["Participant"] = relationship(
        "Participant", back_populates="plans"
    )
    support_categories: Mapped[list["SupportCategory"]] = relationship(
        "SupportCategory", back_populates="plan", cascade="all, delete-orphan"
    )
    invoices = relationship("Invoice", back_populates="plan")


class SupportCategory(Base):
    __tablename__ = "support_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False
    )
    ndis_support_category: Mapped[str] = mapped_column(String(200), nullable=False)
    ndis_support_number: Mapped[str | None] = mapped_column(String(10), nullable=True)
    budget_allocated: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    budget_spent: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )

    plan: Mapped["Plan"] = relationship("Plan", back_populates="support_categories")
    invoice_line_items = relationship("InvoiceLineItem", back_populates="support_category")

    @property
    def budget_remaining(self) -> Decimal:
        """Computed remaining budget."""
        return self.budget_allocated - self.budget_spent

    @property
    def utilisation_percent(self) -> float:
        """Computed utilisation as a percentage."""
        if not self.budget_allocated:
            return 0.0
        return float(self.budget_spent / self.budget_allocated * 100)

    @property
    def is_overspent(self) -> bool:
        """True when budget_spent exceeds budget_allocated."""
        return self.budget_spent > self.budget_allocated
