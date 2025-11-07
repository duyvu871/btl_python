# Assuming this is the UserSubscription model file
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import func

from src.core.database.db import Base

if TYPE_CHECKING:
    from .user import User
    from .plan import Plan

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False)
    cycle_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0))
    cycle_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: (datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0) + timedelta(days=30)))
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    used_seconds: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="subscription")
    plan: Mapped["Plan"] = relationship("Plan")

    __table_args__ = (
        UniqueConstraint("user_id", name="unique_user_subscription"),
        # Keep existing unique for cycle if needed: UniqueConstraint("user_id", "cycle_start", name="unique_user_cycle")
    )
