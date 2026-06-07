from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

router = APIRouter()


@router.get("")
async def list_policies(db: AsyncSession = Depends(get_db)):
    return []


@router.post("", status_code=201)
async def create_policy(db: AsyncSession = Depends(get_db)):
    return {}
