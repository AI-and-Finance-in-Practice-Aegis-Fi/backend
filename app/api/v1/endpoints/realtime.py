"""
Server-Sent Events (SSE) endpoints for real-time dashboard updates.

Architecture:
  - Each generator opens a fresh AsyncSession per poll tick so it never
    holds an idle DB connection between sleeps.
  - Keepalive comments are sent every cycle to prevent proxy/nginx timeouts.
  - The transaction stream anchors to the max transaction_id at connection
    time so only truly new rows are delivered to the client.
"""
import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sqlalchemy import func, not_, select

from app.core.database import AsyncSessionLocal
from app.models.approval_log import ApprovalLog
from app.models.department import Department
from app.models.employee import Employee
from app.models.transaction import Transaction

router = APIRouter()

_POLL_INTERVAL = 5  # seconds


def _sse(data: dict, event: str | None = None) -> str:
    lines = []
    if event:
        lines.append(f"event: {event}")
    lines.append(f"data: {json.dumps(data, ensure_ascii=False, default=str)}")
    return "\n".join(lines) + "\n\n"


# ── /transactions ─────────────────────────────────────────────────────────────

async def _transaction_stream():
    # Anchor: only push transactions inserted AFTER this connection opens.
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(func.max(Transaction.transaction_id)))
        last_id: int = result.scalar() or 0

    yield _sse({"status": "connected", "last_id": last_id}, event="connected")

    while True:
        await asyncio.sleep(_POLL_INTERVAL)
        yield ": keepalive\n\n"

        try:
            async with AsyncSessionLocal() as db:
                stmt = (
                    select(
                        Transaction,
                        Employee.employee_name,
                        Department.department_name,
                    )
                    .join(Employee, Transaction.employee_id == Employee.employee_id)
                    .join(Department, Employee.department_id == Department.department_id)
                    .where(Transaction.transaction_id > last_id)
                    .order_by(Transaction.transaction_id)
                )
                rows = (await db.execute(stmt)).all()

            for tx, emp_name, dept_name in rows:
                payload = {
                    "transaction_id": tx.transaction_id,
                    "merchant_name": tx.merchant_name,
                    "amount": float(tx.amount),
                    "is_approved": tx.is_approved,
                    "department_name": dept_name,
                    "employee_name": emp_name,
                    "payment_time": tx.payment_time.isoformat(),
                }
                yield _sse(payload, event="transaction")
                last_id = tx.transaction_id

        except Exception as exc:
            yield _sse({"error": str(exc)}, event="error")


@router.get("/transactions")
async def stream_transactions():
    return StreamingResponse(
        _transaction_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ── /dashboard-summary ────────────────────────────────────────────────────────

async def _dashboard_summary_stream():
    while True:
        try:
            async with AsyncSessionLocal() as db:
                today_start = datetime.now(timezone.utc).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )

                # Total approved spending today
                res = await db.execute(
                    select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                        Transaction.is_approved == True,  # noqa: E712
                        Transaction.payment_time >= today_start,
                    )
                )
                total_spending_today = float(res.scalar())

                # Blocked (denied) transactions today
                res = await db.execute(
                    select(func.count(Transaction.transaction_id)).where(
                        Transaction.is_approved == False,  # noqa: E712
                        Transaction.payment_time >= today_start,
                    )
                )
                blocked_count_today = int(res.scalar())

                # Approved by policy but no human approval log yet
                logged_ids = select(ApprovalLog.transaction_id)
                res = await db.execute(
                    select(func.count(Transaction.transaction_id)).where(
                        Transaction.is_approved == True,  # noqa: E712
                        not_(Transaction.transaction_id.in_(logged_ids)),
                    )
                )
                pending_approval_count = int(res.scalar())

                # Department budget status
                dept_rows = (
                    await db.execute(
                        select(
                            Department.department_name,
                            Department.current_spending,
                            Department.monthly_budget_limit,
                        ).order_by(Department.department_id)
                    )
                ).all()

                department_budgets = [
                    {
                        "department_name": name,
                        "current_spending": float(spending or 0),
                        "monthly_budget_limit": float(limit or 0),
                    }
                    for name, spending, limit in dept_rows
                ]

            payload = {
                "total_spending_today": total_spending_today,
                "blocked_count_today": blocked_count_today,
                "pending_approval_count": pending_approval_count,
                "department_budgets": department_budgets,
            }
            yield _sse(payload, event="dashboard-summary")

        except Exception as exc:
            yield _sse({"error": str(exc)}, event="error")

        await asyncio.sleep(_POLL_INTERVAL)
        yield ": keepalive\n\n"


@router.get("/dashboard-summary")
async def stream_dashboard_summary():
    return StreamingResponse(
        _dashboard_summary_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
