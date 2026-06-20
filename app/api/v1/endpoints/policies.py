from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.policy import AIPaymentPolicy

router = APIRouter()


@router.get("")
async def list_policies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AIPaymentPolicy))
    policies = result.scalars().all()
    return [
        {
            "policy_id": p.policy_id,
            "employee_id": p.employee_id,
            "department_id": p.department_id,
            "restricted_category": p.restricted_category,
            "single_payment_limit": float(p.single_payment_limit) if p.single_payment_limit is not None else None,
            "is_blocked": p.is_blocked,
        }
        for p in policies
    ]


@router.post("", status_code=201)
async def create_policy(db: AsyncSession = Depends(get_db)):
    return {}
