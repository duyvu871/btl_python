from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import func

from src.core.database.db import Base

if TYPE_CHECKING:
    from .user_subscription import UserSubscription

class PlanType(PyEnum):
    FREE = "FREE"
    BASIC = "BASIC"
    PREMIUM = "PREMIUM"
    ENTERPRISE = "ENTERPRISE"

class BillingCycle(PyEnum):
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"
    LIFETIME = "LIFETIME"

class Plan(Base):
    """Plan model for subscriptions."""

    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False
    )
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan_type: Mapped[PlanType] = mapped_column(Enum(PlanType, name='plan_type'), nullable=False, default=PlanType.FREE)
    billing_cycle: Mapped[BillingCycle] = mapped_column(Enum(BillingCycle, name='billing_cycle'), nullable=False, default=BillingCycle.MONTHLY)
    plan_cost: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    plan_discount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    monthly_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    monthly_usage_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    subscriptions: Mapped[list["UserSubscription"]] = relationship("UserSubscription", back_populates="plan")
