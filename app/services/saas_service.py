from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.saas_subscription import RiskLevel, SaasSubscription
from app.models.saas_usage import SaasUsage
from app.schemas.saas import (
    GhostAccountResponse,
    SubscriptionCreate,
    SubscriptionUpdate,
    UsageCreate,
)

_GHOST_THRESHOLD_DAYS = 45


# ── Pure business logic ───────────────────────────────────────────────────────

def _compute_waste_and_risk(
    monthly_fee: Decimal, total_seats: int, used_seats: int
) -> tuple[Decimal, RiskLevel]:
    if total_seats == 0 or monthly_fee == 0:
        return Decimal(0), RiskLevel.LOW

    wasted = (monthly_fee * (total_seats - used_seats) / total_seats).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    ratio = wasted / monthly_fee

    if ratio > Decimal("0.3"):
        risk = RiskLevel.HIGH
    elif ratio > Decimal("0.1"):
        risk = RiskLevel.MEDIUM
    else:
        risk = RiskLevel.LOW

    return wasted, risk


def _compute_ghost(last_login_date: date | None) -> bool:
    if last_login_date is None:
        return True
    return (date.today() - last_login_date).days >= _GHOST_THRESHOLD_DAYS


# ── Subscription CRUD ─────────────────────────────────────────────────────────

async def create_subscription(
    db: AsyncSession, data: SubscriptionCreate
) -> SaasSubscription:
    wasted, risk = _compute_waste_and_risk(
        data.monthly_fee, data.total_seats, data.used_seats
    )
    sub = SaasSubscription(
        subscription_name=data.subscription_name,
        provider=data.provider,
        monthly_fee=data.monthly_fee,
        total_seats=data.total_seats,
        used_seats=data.used_seats,
        wasted_amount=wasted,
        risk_level=risk,
        renewal_date=data.renewal_date,
        department_id=data.department_id,
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub


async def list_subscriptions(
    db: AsyncSession, department_id: int | None = None
) -> list[SaasSubscription]:
    stmt = select(SaasSubscription)
    if department_id is not None:
        stmt = stmt.where(SaasSubscription.department_id == department_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_subscription(db: AsyncSession, subscription_id: int) -> SaasSubscription:
    sub = await db.get(SaasSubscription, subscription_id)
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription {subscription_id} not found",
        )
    return sub


async def update_subscription(
    db: AsyncSession, subscription_id: int, data: SubscriptionUpdate
) -> SaasSubscription:
    sub = await get_subscription(db, subscription_id)

    update_fields = data.model_dump(exclude_none=True)
    for field, value in update_fields.items():
        setattr(sub, field, value)

    # Recalculate derived fields whenever any seat/fee value changes
    sub.wasted_amount, sub.risk_level = _compute_waste_and_risk(
        sub.monthly_fee, sub.total_seats, sub.used_seats
    )

    await db.commit()
    await db.refresh(sub)
    return sub


async def delete_subscription(db: AsyncSession, subscription_id: int) -> None:
    sub = await get_subscription(db, subscription_id)
    await db.delete(sub)
    await db.commit()


# ── Ghost accounts ────────────────────────────────────────────────────────────

async def list_ghost_accounts(db: AsyncSession) -> list[GhostAccountResponse]:
    stmt = (
        select(SaasUsage)
        .where(SaasUsage.is_ghost_account == True)  # noqa: E712
        .options(selectinload(SaasUsage.subscription))
    )
    result = await db.execute(stmt)
    usages = result.scalars().all()

    return [
        GhostAccountResponse(
            usage_id=u.usage_id,
            employee_id=u.employee_id,
            subscription_id=u.subscription_id,
            subscription_name=u.subscription.subscription_name,
            last_login_date=u.last_login_date,
            monthly_usage_count=u.monthly_usage_count,
            is_ghost_account=u.is_ghost_account,
        )
        for u in usages
    ]


# ── Usage upsert ──────────────────────────────────────────────────────────────

async def upsert_usage(db: AsyncSession, data: UsageCreate) -> SaasUsage:
    # Check subscription exists
    sub = await db.get(SaasSubscription, data.subscription_id)
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription {data.subscription_id} not found",
        )

    # Try to find existing usage record for this (employee, subscription) pair
    stmt = select(SaasUsage).where(
        SaasUsage.employee_id == data.employee_id,
        SaasUsage.subscription_id == data.subscription_id,
    )
    result = await db.execute(stmt)
    usage = result.scalar_one_or_none()

    is_ghost = _compute_ghost(data.last_login_date)

    if usage is not None:
        usage.last_login_date = data.last_login_date
        usage.monthly_usage_count = data.monthly_usage_count
        usage.is_ghost_account = is_ghost
    else:
        usage = SaasUsage(
            employee_id=data.employee_id,
            subscription_id=data.subscription_id,
            last_login_date=data.last_login_date,
            monthly_usage_count=data.monthly_usage_count,
            is_ghost_account=is_ghost,
        )
        db.add(usage)

    await db.commit()
    await db.refresh(usage)
    return usage
