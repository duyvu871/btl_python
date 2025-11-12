# Assuming this is the UserSubscription model file
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database.db import Base

if TYPE_CHECKING:
    from .plan import Plan
    from .user import User

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("plans.id", ondelete="SET NULL"), nullable=True)

    # Snapshot fields to giữ nguyên quota tới hết cycle nếu plan bị deactivate / delete
    plan_code_snapshot: Mapped[str] = mapped_column(String, nullable=False)
    plan_name_snapshot: Mapped[str] = mapped_column(String, nullable=False)
    plan_monthly_minutes_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    plan_monthly_usage_limit_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)

    cycle_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0))
    cycle_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: (datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0) + timedelta(days=30)))

    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    used_seconds: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="subscription", passive_deletes=True)
    plan: Mapped[Optional["Plan"]] = relationship("Plan", back_populates="subscriptions", passive_deletes=True)

    __table_args__ = (
        UniqueConstraint("user_id", name="unique_user_subscription"),
    )

    def apply_plan_snapshot(self, plan: "Plan") -> None:
        """Cập nhật snapshot fields từ Plan khi create / change plan.
        """
        self.plan_id = plan.id
        self.plan_code_snapshot = plan.code
        self.plan_name_snapshot = plan.name
        self.plan_monthly_minutes_snapshot = plan.monthly_minutes
        self.plan_monthly_usage_limit_snapshot = plan.monthly_usage_limit

