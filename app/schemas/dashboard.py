from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TodayStats(BaseModel):
    total_spending: float
    transaction_count: int
    blocked_count: int
    approved_count: int


class SaasStats(BaseModel):
    total_monthly_fee: float
    total_wasted_amount: float
    high_risk_count: int
    ghost_account_count: int


class DepartmentBudget(BaseModel):
    department_id: int
    department_name: str
    monthly_budget_limit: float
    current_spending: float
    spend_rate: float


class DashboardSummaryResponse(BaseModel):
    today: TodayStats
    saas: SaasStats
    pending_approval_count: int
    anomaly_count: int
    department_budgets: list[DepartmentBudget]


class RecentTransactionItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transaction_id: int
    employee_id: int
    employee_name: str
    department_id: int
    department_name: str
    merchant_name: str
    amount: float
    category: str
    is_approved: bool | None
    payment_time: datetime
