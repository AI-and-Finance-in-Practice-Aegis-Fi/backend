"""
Rule-based payment policy engine.
No LLM — pure conditional logic against AIPaymentPolicy table.

Policy semantics:
  is_blocked=True  + restricted_category      → category is completely prohibited
  is_blocked=True  + restricted_category=None → employee/dept is globally blocked
  is_blocked=False + restricted_category      → category has a single_payment_limit

Evaluation order (per CLAUDE.md):
  1. Global block   : is_blocked=True, no category  → deny immediately
  2. Category block : is_blocked=True, category matches → deny
  3. Amount limit   : is_blocked=False, category matches, amount > limit → deny
  4. All pass → approve
"""
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.models.policy import AIPaymentPolicy


@dataclass(frozen=True)
class PolicyResult:
    is_approved: bool
    reason: str


async def evaluate(
    db: AsyncSession,
    employee_id: int,
    category: str,
    amount: Decimal,
) -> PolicyResult:
    # ── Resolve employee → department ─────────────────────────────────────────
    employee = await db.get(Employee, employee_id)
    if employee is None:
        return PolicyResult(
            is_approved=False,
            reason=f"employee_id={employee_id} 직원 정보를 찾을 수 없습니다.",
        )

    department_id = employee.department_id

    # ── Load all policies applicable to this employee / department ────────────
    result = await db.execute(
        select(AIPaymentPolicy).where(
            or_(
                AIPaymentPolicy.employee_id == employee_id,
                AIPaymentPolicy.department_id == department_id,
            )
        )
    )
    policies: list[AIPaymentPolicy] = list(result.scalars().all())

    if not policies:
        return PolicyResult(
            is_approved=True,
            reason="적용된 결제 정책이 없습니다. 결제가 승인되었습니다.",
        )

    category_lower = category.lower()

    # ── Rule 1: Global block (is_blocked=True, no category restriction) ───────
    # A policy with is_blocked=True and no restricted_category
    # means the employee or their entire department is blocked.
    global_blocked = [
        p for p in policies
        if p.is_blocked and p.restricted_category is None
    ]
    if global_blocked:
        return PolicyResult(
            is_approved=False,
            reason="해당 직원 또는 부서에 전면 결제 차단 정책이 적용되어 있습니다.",
        )

    # ── Rule 2: Category block (is_blocked=True + category matches) ───────────
    category_blocked = [
        p for p in policies
        if p.is_blocked
        and p.restricted_category is not None
        and p.restricted_category.lower() == category_lower
    ]
    if category_blocked:
        return PolicyResult(
            is_approved=False,
            reason=f"카테고리 '{category}'는 정책에 의해 차단된 결제 항목입니다.",
        )

    # ── Rule 3: Amount limit (is_blocked=False + category matches + over limit) ─
    limit_exceeded = [
        p for p in policies
        if not p.is_blocked
        and p.restricted_category is not None
        and p.restricted_category.lower() == category_lower
        and p.single_payment_limit is not None
        and amount > p.single_payment_limit
    ]
    if limit_exceeded:
        tightest = min(p.single_payment_limit for p in limit_exceeded)
        return PolicyResult(
            is_approved=False,
            reason=(
                f"결제 금액({int(amount):,}원)이 "
                f"1회 결제 한도({int(tightest):,}원)를 초과합니다."
            ),
        )

    # ── Rule 4: All checks passed → approve ───────────────────────────────────
    return PolicyResult(
        is_approved=True,
        reason="정책 검토 통과: 결제가 승인되었습니다.",
    )
