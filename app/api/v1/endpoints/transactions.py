from datetime import date

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.transaction import (
    TransactionDetailResponse,
    TransactionListItem,
    TransactionRequest,
    TransactionRequestResponse,
)
from app.services import transaction_service

router = APIRouter()


@router.post(
    "/request",
    response_model=TransactionRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_transaction(
    body: TransactionRequest,
    db: AsyncSession = Depends(get_db),
):
    return await transaction_service.request_transaction(db, body)


@router.get("", response_model=list[TransactionListItem])
async def list_transactions(
    employee_id: int | None = None,
    department_id: int | None = None,
    is_approved: bool | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await transaction_service.list_transactions(
        db,
        employee_id=employee_id,
        department_id=department_id,
        is_approved=is_approved,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/{transaction_id}", response_model=TransactionDetailResponse)
async def get_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await transaction_service.get_transaction(db, transaction_id)
