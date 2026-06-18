from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approval_log import ApprovalLog
from app.models.department import Department
from app.models.employee import Employee
from app.models.saas_subscription import RiskLevel, SaasSubscription
from app.models.saas_usage import SaasUsage
from app.models.transaction import Transaction
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    DepartmentBudget,
    RecentTransactionItem,
    SaasStats,
    TodayStats,
)
from app.services import anomaly_detection


async def get_summary(db: AsyncSession) -> DashboardSummaryResponse:
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    # ── Today stats ───────────────────────────────────────────────────────────
    row = (
        await db.execute(
            select(
                func.coalesce(
                    func.sum(Transaction.amount).filter(
                        Transaction.is_approved == True  # noqa: E712
                    ),
                    0,
                ).label("total_spending"),
                func.count(Transaction.transaction_id).label("transaction_count"),
                func.count(Transaction.transaction_id)
                .filter(Transaction.is_approved == False)  # noqa: E712
                .label("blocked_count"),
                func.count(Transaction.transaction_id)
                .filter(Transaction.is_approved == True)  # noqa: E712
                .label("approved_count"),
            ).where(Transaction.payment_time >= today_start)
        )
    ).one()

    today = TodayStats(
        total_spending=float(row.total_spending),
        transaction_count=row.transaction_count,
        blocked_count=row.blocked_count,
        approved_count=row.approved_count,
    )

    # ── SaaS stats ────────────────────────────────────────────────────────────
    saas_row = (
        await db.execute(
            select(
                func.coalesce(func.sum(SaasSubscription.monthly_fee), 0).label(
                    "total_monthly_fee"
                ),
                func.coalesce(func.sum(SaasSubscription.wasted_amount), 0).label(
                    "total_wasted_amount"
                ),
                func.count(SaasSubscription.subscription_id)
                .filter(SaasSubscription.risk_level == RiskLevel.HIGH)
                .label("high_risk_count"),
            )
        )
    ).one()

    ghost_count = (
        await db.execute(
            select(func.count(SaasUsage.usage_id)).where(
                SaasUsage.is_ghost_account == True  # noqa: E712
            )
        )
    ).scalar()

    saas = SaasStats(
        total_monthly_fee=float(saas_row.total_monthly_fee),
        total_wasted_amount=float(saas_row.total_wasted_amount),
        high_risk_count=saas_row.high_risk_count,
        ghost_account_count=int(ghost_count),
    )

    # ── Pending approval count ────────────────────────────────────────────────
    pending_approval_count = (
        await db.execute(
            select(func.count(ApprovalLog.approval_id)).where(
                ApprovalLog.approval_result.is_(None)
            )
        )
    ).scalar()

    # ── Anomaly count (re-uses existing detect logic) ─────────────────────────
    anomaly_results = await anomaly_detection.detect(db)
    anomaly_count = sum(1 for r in anomaly_results if r.is_anomaly)

    # ── Department budgets ────────────────────────────────────────────────────
    dept_rows = (
        await db.execute(
            select(Department).order_by(Department.department_id)
        )
    ).scalars().all()

    department_budgets = [
        DepartmentBudget(
            department_id=d.department_id,
            department_name=d.department_name,
            monthly_budget_limit=float(d.monthly_budget_limit),
            current_spending=float(d.current_spending or 0),
            spend_rate=(
                round(
                    float(d.current_spending or 0) / float(d.monthly_budget_limit), 4
                )
                if d.monthly_budget_limit
                else 0.0
            ),
        )
        for d in dept_rows
    ]

    return DashboardSummaryResponse(
        today=today,
        saas=saas,
        pending_approval_count=int(pending_approval_count),
        anomaly_count=anomaly_count,
        department_budgets=department_budgets,
    )


async def get_recent_transactions(
    db: AsyncSession, limit: int = 20
) -> list[RecentTransactionItem]:
    rows = (
        await db.execute(
            select(
                Transaction,
                Employee.employee_name,
                Department.department_id,
                Department.department_name,
            )
            .join(Employee, Transaction.employee_id == Employee.employee_id)
            .join(Department, Employee.department_id == Department.department_id)
            .order_by(Transaction.payment_time.desc())
            .limit(limit)
        )
    ).all()

    return [
        RecentTransactionItem(
            transaction_id=tx.transaction_id,
            employee_id=tx.employee_id,
            employee_name=emp_name,
            department_id=dept_id,
            department_name=dept_name,
            merchant_name=tx.merchant_name,
            amount=float(tx.amount),
            category=tx.category,
            is_approved=tx.is_approved,
            payment_time=tx.payment_time,
        )
        for tx, emp_name, dept_id, dept_name in rows
    ]
