from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# ── Request / Response for POST /request ─────────────────────────────────────

class TransactionRequest(BaseModel):
    employee_id: int
    merchant_name: str
    amount: Decimal = Field(gt=0)
    category: str
    user_input_reason: str | None = None


class TransactionRequestResponse(BaseModel):
    transaction_id: int
    is_approved: bool
    reason: str


# ── Approval log (embedded in detail response) ────────────────────────────────

class ApprovalLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    approval_id: int
    approver_employee_id: int
    approval_result: bool
    approval_reason: str | None
    approval_time: datetime


# ── List response (includes joined employee / department fields) ───────────────

class TransactionListItem(BaseModel):
    transaction_id: int
    employee_id: int
    employee_name: str
    department_id: int
    department_name: str
    merchant_name: str
    amount: Decimal
    category: str
    user_input_reason: str | None
    is_approved: bool | None
    ai_risk_score: Decimal | None
    ai_risk_reason: str | None
    payment_time: datetime


# ── Detail response (list item + AI fields + approval logs) ──────────────────

class TransactionDetailResponse(TransactionListItem):
    ai_predicted_reason: str | None
    approval_logs: list[ApprovalLogResponse]
