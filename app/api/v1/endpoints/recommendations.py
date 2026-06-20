from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.saas_subscription import SaasSubscription

router = APIRouter()


@router.get("")
async def get_recommendations(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(SaasSubscription)
        .where(SaasSubscription.risk_level == "HIGH")
        .order_by(SaasSubscription.wasted_amount.desc())
        .limit(10)
    )
    result = await db.execute(stmt)
    subs = result.scalars().all()

    return [
        {
            "subscription_id": sub.subscription_id,
            "subscription_name": sub.subscription_name,
            "provider": sub.provider,
            "monthly_fee": float(sub.monthly_fee or 0),
            "total_seats": sub.total_seats,
            "used_seats": sub.used_seats,
            "wasted_amount": float(sub.wasted_amount or 0),
            "risk_level": sub.risk_level,
            "renewal_date": str(sub.renewal_date) if sub.renewal_date else None,
            "recommendation": (
                f"{sub.subscription_name} 구독 최적화: "
                f"{sub.total_seats - sub.used_seats}석 미사용 중, "
                f"월 {int(float(sub.wasted_amount or 0)):,}원 절감 가능"
            ),
        }
        for sub in subs
    ]
