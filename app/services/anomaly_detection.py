"""
Z-score based department spending anomaly detection.
Pure Python — no external statistical libraries.

Algorithm:
  1. Aggregate approved Transaction amounts by department × month
     for the window [current_month - 3, current_month).
  2. Compute mean and population std of the 3-month baseline.
  3. Z-score = (current_month_spending - mean) / std
     - If std == 0 (identical baseline values or <2 months data) → Z-score = 0
  4. is_anomaly = Z-score > 2.0
"""
import math
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.department import Department
from app.models.employee import Employee
from app.models.transaction import Transaction
from app.schemas.report import AnomalyResult

_ANOMALY_THRESHOLD = 2.0


# ── Pure math helpers ─────────────────────────────────────────────────────────

def _population_std(values: list[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    return math.sqrt(sum((x - mean) ** 2 for x in values) / n)


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _month_key(dt: datetime) -> tuple[int, int]:
    """Return (year, month) for grouping."""
    return dt.year, dt.month


def _subtract_months(year: int, month: int, n: int) -> tuple[int, int]:
    """Go back n months from (year, month) without external libraries."""
    month -= n
    while month <= 0:
        month += 12
        year -= 1
    return year, month


# ── Main service function ─────────────────────────────────────────────────────

async def detect(db: AsyncSession) -> list[AnomalyResult]:
    now = datetime.now(timezone.utc)
    current_ym = (now.year, now.month)

    # Start of current month (UTC)
    current_month_start = now.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    # Start of the 3-month baseline window
    base_year, base_month = _subtract_months(now.year, now.month, 3)
    baseline_start = current_month_start.replace(year=base_year, month=base_month)

    # Build the 3-month baseline keys (not including current month)
    baseline_months: list[tuple[int, int]] = []
    for offset in range(3, 0, -1):
        y, m = _subtract_months(now.year, now.month, offset)
        baseline_months.append((y, m))

    # ── Query: approved transactions grouped by dept × month ──────────────────
    month_trunc = func.date_trunc("month", Transaction.payment_time)

    stmt = (
        select(
            Department.department_id,
            Department.department_name,
            month_trunc.label("month"),
            func.sum(Transaction.amount).label("total"),
        )
        .join(Employee, Transaction.employee_id == Employee.employee_id)
        .join(Department, Employee.department_id == Department.department_id)
        .where(
            Transaction.is_approved == True,  # noqa: E712
            Transaction.payment_time >= baseline_start,
        )
        .group_by(
            Department.department_id,
            Department.department_name,
            month_trunc,
        )
        .order_by(Department.department_id, month_trunc)
    )

    rows = (await db.execute(stmt)).all()

    # ── Organise spending by dept → month → amount ────────────────────────────
    # dept_info: {dept_id: dept_name}
    # spending:  {dept_id: {(year, month): float}}
    dept_info: dict[int, str] = {}
    spending: dict[int, dict[tuple[int, int], float]] = defaultdict(dict)

    for dept_id, dept_name, month_dt, total in rows:
        dept_info[dept_id] = dept_name
        ym = _month_key(month_dt)
        spending[dept_id][ym] = float(total)

    # Also include departments that have zero transactions in the window
    all_depts = (await db.execute(
        select(Department.department_id, Department.department_name)
    )).all()
    for dept_id, dept_name in all_depts:
        dept_info.setdefault(dept_id, dept_name)
        spending.setdefault(dept_id, {})

    # ── Compute Z-scores ──────────────────────────────────────────────────────
    results: list[AnomalyResult] = []

    for dept_id, dept_name in sorted(dept_info.items()):
        dept_spending = spending[dept_id]

        # Baseline = the 3 months before the current month (fill missing with 0)
        baseline_values = [
            dept_spending.get(ym, 0.0) for ym in baseline_months
        ]
        current = dept_spending.get(current_ym, 0.0)

        mean_val = _mean(baseline_values)
        std_val = _population_std(baseline_values)

        if std_val == 0.0:
            z_score = 0.0
        else:
            z_score = (current - mean_val) / std_val

        results.append(
            AnomalyResult(
                department_id=dept_id,
                department_name=dept_name,
                current_spending=round(current, 2),
                mean_spending=round(mean_val, 2),
                z_score=round(z_score, 4),
                is_anomaly=z_score > _ANOMALY_THRESHOLD,
                excess_amount=round(max(0.0, current - mean_val), 2),
            )
        )

    return results
