from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.department import Department
from app.models.employee import Employee
from app.models.transaction import Transaction
from app.schemas.transaction import (
    ApprovalLogResponse,
    TransactionDetailResponse,
    TransactionListItem,
    TransactionRequest,
    TransactionRequestResponse,
)
from app.models.approval_log import ApprovalLog
from app.services import audit_service, policy_engine


async def request_transaction(
    db: AsyncSession, data: TransactionRequest
) -> TransactionRequestResponse:
    # ── 1. Policy check ───────────────────────────────────────────────────────
    result = await policy_engine.evaluate(
        db,
        employee_id=data.employee_id,
        category=data.category,
        amount=data.amount,
    )

    # ── 2. Persist transaction ────────────────────────────────────────────────
    tx = Transaction(
        employee_id=data.employee_id,
        merchant_name=data.merchant_name,
        amount=data.amount,
        category=data.category,
        user_input_reason=data.user_input_reason,
        is_approved=result.is_approved,
        ai_risk_reason=result.reason,
        payment_time=datetime.now(timezone.utc),
    )
    db.add(tx)
    await db.flush()  # get transaction_id before department update

    # ── 3. Update department spending only on approval ────────────────────────
    if result.is_approved:
        employee = await db.get(Employee, data.employee_id)
        dept = await db.get(Department, employee.department_id)
        dept.current_spending = (dept.current_spending or Decimal(0)) + data.amount

    # ── 4. Auto-create pending ApprovalLog so finance team sees blocked tx ────
    if not result.is_approved:
        pending_log = ApprovalLog(
            transaction_id=tx.transaction_id,
            approver_employee_id=None,
            approval_result=None,
            approval_reason=result.reason,
            approval_time=None,
        )
        db.add(pending_log)

    event_type = (
        "TRANSACTION_APPROVED" if result.is_approved else "TRANSACTION_BLOCKED"
    )
    await audit_service.record(
        db,
        event_type=event_type,
        event_data_dict={
            "transaction_id": tx.transaction_id,
            "employee_id": tx.employee_id,
            "merchant_name": tx.merchant_name,
            "amount": str(tx.amount),
            "category": tx.category,
            "is_approved": tx.is_approved,
            "reason": result.reason,
        },
    )

    await db.commit()
    await db.refresh(tx)

    return TransactionRequestResponse(
        transaction_id=tx.transaction_id,
        is_approved=result.is_approved,
        reason=result.reason,
    )


async def list_transactions(
    db: AsyncSession,
    employee_id: int | None = None,
    department_id: int | None = None,
    is_approved: bool | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[TransactionListItem]:
    stmt = (
        select(
            Transaction,
            Employee.employee_name,
            Department.department_id,
            Department.department_name,
        )
        .join(Employee, Transaction.employee_id == Employee.employee_id)
        .join(Department, Employee.department_id == Department.department_id)
        .order_by(Transaction.payment_time.desc())
    )

    if employee_id is not None:
        stmt = stmt.where(Transaction.employee_id == employee_id)
    if department_id is not None:
        stmt = stmt.where(Department.department_id == department_id)
    if is_approved is not None:
        stmt = stmt.where(Transaction.is_approved == is_approved)
    if start_date is not None:
        stmt = stmt.where(
            Transaction.payment_time >= datetime.combine(start_date, datetime.min.time())
        )
    if end_date is not None:
        stmt = stmt.where(
            Transaction.payment_time <= datetime.combine(end_date, datetime.max.time())
        )

    rows = (await db.execute(stmt)).all()

    return [
        TransactionListItem(
            transaction_id=tx.transaction_id,
            employee_id=tx.employee_id,
            employee_name=emp_name,
            department_id=dept_id,
            department_name=dept_name,
            merchant_name=tx.merchant_name,
            amount=tx.amount,
            category=tx.category,
            user_input_reason=tx.user_input_reason,
            is_approved=tx.is_approved,
            ai_risk_score=tx.ai_risk_score,
            ai_risk_reason=tx.ai_risk_reason,
            payment_time=tx.payment_time,
        )
        for tx, emp_name, dept_id, dept_name in rows
    ]


async def get_transaction(
    db: AsyncSession, transaction_id: int
) -> TransactionDetailResponse:
    stmt = (
        select(
            Transaction,
            Employee.employee_name,
            Department.department_id,
            Department.department_name,
        )
        .join(Employee, Transaction.employee_id == Employee.employee_id)
        .join(Department, Employee.department_id == Department.department_id)
        .where(Transaction.transaction_id == transaction_id)
        .options(selectinload(Transaction.approval_logs))
    )

    row = (await db.execute(stmt)).first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found",
        )

    tx, emp_name, dept_id, dept_name = row

    return TransactionDetailResponse(
        transaction_id=tx.transaction_id,
        employee_id=tx.employee_id,
        employee_name=emp_name,
        department_id=dept_id,
        department_name=dept_name,
        merchant_name=tx.merchant_name,
        amount=tx.amount,
        category=tx.category,
        user_input_reason=tx.user_input_reason,
        ai_predicted_reason=tx.ai_predicted_reason,
        is_approved=tx.is_approved,
        ai_risk_score=tx.ai_risk_score,
        ai_risk_reason=tx.ai_risk_reason,
        payment_time=tx.payment_time,
        approval_logs=[
            ApprovalLogResponse(
                approval_id=log.approval_id,
                approver_employee_id=log.approver_employee_id,
                approval_result=log.approval_result,
                approval_reason=log.approval_reason,
                approval_time=log.approval_time,
            )
            for log in tx.approval_logs
        ],
    )
