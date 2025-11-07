from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import func

from src.core.database.db import Base

if TYPE_CHECKING:
    """
    Type checking imports to avoid circular dependencies.
    """
    from .user_profile import UserProfile
    from .user_subscription import UserSubscription
    from .recording import Recording

class Role(PyEnum):
    USER = "user"
    ADMIN = "admin"

class UserStatus(PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BANNED = "banned"

class User(Base):
    """User model representing a user in the system."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False
    )
    user_name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, unique=False, nullable=False, default=False)
    password: Mapped[str] = mapped_column(String, nullable=False)  # Hashed password
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.USER, nullable=False)
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    profile: Mapped["UserProfile"] = relationship("UserProfile", back_populates="user", uselist=False)
    subscriptions: Mapped[list["UserSubscription"]] = relationship("UserSubscription", back_populates="user")
    recordings: Mapped[list["Recording"]] = relationship("Recording", back_populates="user")
