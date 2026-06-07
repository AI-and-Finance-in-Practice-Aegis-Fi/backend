from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.dashboard import DashboardSummaryResponse, RecentTransactionItem
from app.services import dashboard_service

router = APIRouter()


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    return await dashboard_service.get_summary(db)


@router.get("/transactions/recent", response_model=list[RecentTransactionItem])
async def get_recent_transactions(db: AsyncSession = Depends(get_db)):
    return await dashboard_service.get_recent_transactions(db)
