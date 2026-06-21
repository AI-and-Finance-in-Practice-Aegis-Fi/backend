from datetime import datetime

from pydantic import BaseModel


# ── POST /{transaction_id}/request ────────────────────────────────────────────

class ApprovalRequestBody(BaseModel):
    reason: str


class ApprovalRequestResponse(BaseModel):
    approval_id: int
    transaction_id: int
    status: str  # "pending"


# ── PUT /{approval_id}/decide ─────────────────────────────────────────────────

class ApprovalDecideBody(BaseModel):
    decision: bool
    approver_employee_id: int | None = None
    reason: str


class ApprovalDecideResponse(BaseModel):
    approval_id: int
    transaction_id: int
    decision: bool
    approval_time: datetime


# ── GET /pending ──────────────────────────────────────────────────────────────

class PendingApprovalItem(BaseModel):
    approval_id: int
    transaction_id: int
    employee_name: str
    department_name: str
    merchant_name: str
    amount: float
    approval_reason: str | None
    requested_at: datetime  # ApprovalLog.created_at


# ── GET /{approval_id} ────────────────────────────────────────────────────────

class ApprovalDetailResponse(BaseModel):
    approval_id: int
    transaction_id: int
    approver_employee_id: int | None
    approval_result: bool | None
    approval_reason: str | None
    approval_time: datetime | None
    requested_at: datetime
    employee_name: str
    department_name: str
    merchant_name: str
    amount: float
    category: str
