from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.saas import (
    GhostAccountResponse,
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionUpdate,
    UsageCreate,
    UsageResponse,
)
from app.services import saas_service

router = APIRouter()


# ── Subscriptions ─────────────────────────────────────────────────────────────

@router.post(
    "/subscriptions",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_subscription(
    body: SubscriptionCreate,
    db: AsyncSession = Depends(get_db),
):
    return await saas_service.create_subscription(db, body)


@router.get("/subscriptions", response_model=list[SubscriptionResponse])
async def list_subscriptions(
    department_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await saas_service.list_subscriptions(db, department_id=department_id)


@router.get("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await saas_service.get_subscription(db, subscription_id)


@router.put("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: int,
    body: SubscriptionUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await saas_service.update_subscription(db, subscription_id, body)


@router.delete(
    "/subscriptions/{subscription_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_subscription(
    subscription_id: int,
    db: AsyncSession = Depends(get_db),
):
    await saas_service.delete_subscription(db, subscription_id)


# ── Ghost accounts ────────────────────────────────────────────────────────────

@router.get("/ghost-accounts", response_model=list[GhostAccountResponse])
async def list_ghost_accounts(db: AsyncSession = Depends(get_db)):
    return await saas_service.list_ghost_accounts(db)


# ── Usage ─────────────────────────────────────────────────────────────────────

@router.post(
    "/usage",
    response_model=UsageResponse,
    status_code=status.HTTP_200_OK,
)
async def upsert_usage(
    body: UsageCreate,
    db: AsyncSession = Depends(get_db),
):
    return await saas_service.upsert_usage(db, body)
