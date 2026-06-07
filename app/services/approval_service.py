from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approval_log import ApprovalLog
from app.models.department import Department
from app.models.employee import Employee
from app.models.transaction import Transaction
from app.schemas.approval import (
    ApprovalDecideBody,
    ApprovalDecideResponse,
    ApprovalDetailResponse,
    ApprovalRequestResponse,
    PendingApprovalItem,
)
from app.services import audit_service


async def request_exception(
    db: AsyncSession,
    transaction_id: int,
    reason: str,
) -> ApprovalRequestResponse:
    tx = await db.get(Transaction, transaction_id)
    if tx is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found",
        )
    if tx.is_approved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already approved transactions cannot request exception approval",
        )

    log = ApprovalLog(
        transaction_id=transaction_id,
        approver_employee_id=None,
        approval_result=None,
        approval_reason=reason,
        approval_time=None,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)

    return ApprovalRequestResponse(
        approval_id=log.approval_id,
        transaction_id=transaction_id,
        status="pending",
    )


async def decide(
    db: AsyncSession,
    approval_id: int,
    body: ApprovalDecideBody,
) -> ApprovalDecideResponse:
    log = await db.get(ApprovalLog, approval_id)
    if log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ApprovalLog {approval_id} not found",
        )
    if log.approval_result is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This approval request has already been decided",
        )

    now = datetime.now(timezone.utc)
    log.approval_result = body.decision
    log.approver_employee_id = body.approver_employee_id
    log.approval_reason = body.reason
    log.approval_time = now

    if body.decision:
        tx = await db.get(Transaction, log.transaction_id)
        if tx is not None:
            tx.is_approved = True

    event_type = "APPROVAL_GRANTED" if body.decision else "APPROVAL_REJECTED"
    await audit_service.record(
        db,
        event_type=event_type,
        event_data_dict={
            "approval_id": approval_id,
            "transaction_id": log.transaction_id,
            "approver_employee_id": body.approver_employee_id,
            "decision": body.decision,
            "reason": body.reason,
        },
    )

    await db.commit()
    await db.refresh(log)

    return ApprovalDecideResponse(
        approval_id=log.approval_id,
        transaction_id=log.transaction_id,
        decision=log.approval_result,
        approval_time=log.approval_time,
    )


def _pending_join_stmt():
    return (
        select(
            ApprovalLog,
            Employee.employee_name,
            Department.department_name,
            Transaction.merchant_name,
            Transaction.amount,
            Transaction.category,
        )
        .join(Transaction, ApprovalLog.transaction_id == Transaction.transaction_id)
        .join(Employee, Transaction.employee_id == Employee.employee_id)
        .join(Department, Employee.department_id == Department.department_id)
    )


async def list_pending(db: AsyncSession) -> list[PendingApprovalItem]:
    rows = (
        await db.execute(
            _pending_join_stmt()
            .where(ApprovalLog.approval_result.is_(None))
            .order_by(ApprovalLog.created_at.desc())
        )
    ).all()

    return [
        PendingApprovalItem(
            approval_id=log.approval_id,
            transaction_id=log.transaction_id,
            employee_name=emp_name,
            department_name=dept_name,
            merchant_name=merchant_name,
            amount=float(amount),
            approval_reason=log.approval_reason,
            requested_at=log.created_at,
        )
        for log, emp_name, dept_name, merchant_name, amount, _ in rows
    ]


async def get_detail(db: AsyncSession, approval_id: int) -> ApprovalDetailResponse:
    row = (
        await db.execute(
            _pending_join_stmt().where(ApprovalLog.approval_id == approval_id)
        )
    ).first()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ApprovalLog {approval_id} not found",
        )

    log, emp_name, dept_name, merchant_name, amount, category = row

    return ApprovalDetailResponse(
        approval_id=log.approval_id,
        transaction_id=log.transaction_id,
        approver_employee_id=log.approver_employee_id,
        approval_result=log.approval_result,
        approval_reason=log.approval_reason,
        approval_time=log.approval_time,
        requested_at=log.created_at,
        employee_name=emp_name,
        department_name=dept_name,
        merchant_name=merchant_name,
        amount=float(amount),
        category=category,
    )
