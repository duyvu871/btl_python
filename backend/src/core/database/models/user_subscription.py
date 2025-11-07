from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import func

from src.core.database.db import Base

if TYPE_CHECKING:
    from .user import User
    from .plan import Plan


class UserSubscription(Base):
    """User subscription model."""

    __tablename__ = "user_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    cycle_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.date_trunc('month', func.now()))
    cycle_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.date_trunc('month', func.now()) + func.interval('1 month'))
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    used_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="subscriptions")
    plan: Mapped["Plan"] = relationship("Plan", back_populates="subscriptions")
