from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.saas_subscription import RiskLevel


# ── Subscription ──────────────────────────────────────────────────────────────

class SubscriptionCreate(BaseModel):
    subscription_name: str
    provider: str
    monthly_fee: Decimal = Field(gt=0)
    total_seats: int = Field(ge=1)
    used_seats: int = Field(ge=0, default=0)
    renewal_date: date | None = None
    department_id: int


class SubscriptionUpdate(BaseModel):
    subscription_name: str | None = None
    provider: str | None = None
    monthly_fee: Decimal | None = Field(default=None, gt=0)
    total_seats: int | None = Field(default=None, ge=1)
    used_seats: int | None = Field(default=None, ge=0)
    renewal_date: date | None = None
    department_id: int | None = None


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    subscription_id: int
    subscription_name: str
    provider: str
    monthly_fee: Decimal
    total_seats: int
    used_seats: int
    wasted_amount: Decimal
    risk_level: RiskLevel
    renewal_date: date | None
    department_id: int


# ── Ghost accounts ────────────────────────────────────────────────────────────

class GhostAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    usage_id: int
    employee_id: int
    subscription_id: int
    subscription_name: str
    last_login_date: date | None
    monthly_usage_count: int
    is_ghost_account: bool


# ── Usage ─────────────────────────────────────────────────────────────────────

class UsageCreate(BaseModel):
    employee_id: int
    subscription_id: int
    last_login_date: date | None = None
    monthly_usage_count: int = Field(ge=0, default=0)


class UsageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    usage_id: int
    employee_id: int
    subscription_id: int
    last_login_date: date | None
    monthly_usage_count: int
    is_ghost_account: bool
