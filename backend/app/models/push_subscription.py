"""ORM model for storing Web Push subscriptions per participant."""

from sqlalchemy import Column, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import TimestampMixin, UUIDMixin


class PushSubscription(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "push_subscriptions"

    participant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("participants.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    subscription = Column(JSON, nullable=False)

    participant = relationship("Participant")
