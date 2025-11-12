"""
Pydantic schemas for subscription module.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ============================================================================
# Plan Schemas (database plan vs snapshot)
# ============================================================================

class PlanBase(BaseModel):
    code: str
    name: str
    description: str | None = None
    plan_type: str
    plan_cost: int = 0
    plan_discount: int = 0
    monthly_minutes: int = Field(description="Quota minutes for entire billing cycle (month/year)")
    monthly_usage_limit: int = Field(description="Quota usage count for entire billing cycle")
    billing_cycle: str = Field(description="Billing cycle: MONTHLY / YEARLY / LIFETIME")


class PlanResponse(BaseModel):
    """Plan từ bảng plans (dùng cho endpoint /plans)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    description: str | None = None
    plan_type: str
    plan_cost: int
    plan_discount: int
    monthly_minutes: int = Field(description="Quota minutes for entire billing cycle")
    monthly_usage_limit: int = Field(description="Quota usage count for entire billing cycle")
    billing_cycle: str = Field(description="Billing cycle")
    created_at: datetime


class PlanSnapshotResponse(BaseModel):
    """Snapshot plan dùng trong subscription (không phụ thuộc bảng plans)."""
    code: str
    name: str
    monthly_minutes: int
    monthly_usage_limit: int


# ============================================================================
# Usage Statistics Schemas
# ============================================================================

class UsageResponse(BaseModel):
    usage_count: int = Field(description="Number of recordings created this cycle")
    monthly_usage_limit: int = Field(description="Maximum recordings allowed this cycle")
    remaining_count: int = Field(description="Remaining recordings available")
    used_seconds: int = Field(description="Total seconds used this cycle")
    monthly_seconds: int = Field(description="Maximum seconds allowed this cycle")
    remaining_seconds: int = Field(description="Remaining seconds available")
    used_minutes: float = Field(description="Total minutes used (rounded to 2 decimals)")
    monthly_minutes: int = Field(description="Maximum minutes allowed this cycle")
    remaining_minutes: float = Field(description="Remaining minutes available")


# ============================================================================
# Subscription Schemas
# ============================================================================

class SubscriptionResponse(BaseModel):
    """Response cho thay đổi plan / lấy subscription (dùng snapshot)."""
    id: UUID
    user_id: UUID
    plan: PlanSnapshotResponse
    cycle_start: datetime
    cycle_end: datetime
    usage: UsageResponse


class SubscriptionDetailResponse(BaseModel):
    """Detailed subscription information for dashboard (snapshot)."""
    plan: PlanSnapshotResponse
    cycle_start: datetime
    cycle_end: datetime
    usage: UsageResponse


# ============================================================================
# Request Schemas
# ============================================================================

class ChangePlanRequest(BaseModel):
    plan_code: str = Field(description="Plan code to change to (e.g., 'BASIC', 'PREMIUM')")
    prorate: bool = Field(default=False, description="Whether to reset usage on plan change")


# ============================================================================
# Response Schemas
# ============================================================================

class QuotaCheckResponse(BaseModel):
    has_quota: bool
    error_message: str = ""

class ChangePlanResponse(BaseModel):
    message: str
    new_plan: PlanSnapshotResponse
    subscription: SubscriptionResponse
