"""
Pydantic schemas for subscription module.
"""
from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# Plan Schemas
# ============================================================================

class PlanBase(BaseModel):
    """Base schema for Plan."""
    code: str
    name: str
    description: Optional[str] = None
    plan_type: str
    plan_cost: int = 0
    plan_discount: int = 0
    monthly_minutes: int
    monthly_usage_limit: int


class PlanResponse(BaseModel):
    """Response schema for Plan."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    plan_type: str
    plan_cost: int
    plan_discount: int
    monthly_minutes: int
    monthly_usage_limit: int
    created_at: datetime


# ============================================================================
# Usage Statistics Schemas
# ============================================================================

class UsageResponse(BaseModel):
    """Response schema for usage statistics."""
    usage_count: int = Field(description="Number of recordings created this cycle")
    monthly_usage_limit: int = Field(description="Maximum recordings allowed per month")
    remaining_count: int = Field(description="Remaining recordings available")
    used_seconds: int = Field(description="Total seconds used this cycle")
    monthly_seconds: int = Field(description="Maximum seconds allowed per month")
    remaining_seconds: int = Field(description="Remaining seconds available")
    used_minutes: float = Field(description="Total minutes used (rounded to 2 decimals)")
    monthly_minutes: int = Field(description="Maximum minutes allowed per month")
    remaining_minutes: float = Field(description="Remaining minutes available")


# ============================================================================
# Subscription Schemas
# ============================================================================

class SubscriptionResponse(BaseModel):
    """Response schema for user subscription with plan and usage details."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    plan: PlanResponse
    cycle_start: datetime
    cycle_end: datetime
    usage: UsageResponse


class SubscriptionDetailResponse(BaseModel):
    """Detailed subscription information for dashboard."""
    plan: PlanResponse
    cycle_start: datetime
    cycle_end: datetime
    usage: UsageResponse


# ============================================================================
# Request Schemas
# ============================================================================

class ChangePlanRequest(BaseModel):
    """Request schema for changing subscription plan."""
    plan_code: str = Field(description="Plan code to change to (e.g., 'BASIC', 'PREMIUM')")
    prorate: bool = Field(default=False, description="Whether to reset usage on plan change")


# ============================================================================
# Response Schemas
# ============================================================================

class QuotaCheckResponse(BaseModel):
    """Response schema for quota check."""
    has_quota: bool
    error_message: str = ""


class ChangePlanResponse(BaseModel):
    """Response schema for plan change."""
    message: str
    new_plan: PlanResponse
    subscription: SubscriptionResponse

