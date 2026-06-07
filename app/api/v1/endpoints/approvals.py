from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.approval import (
    ApprovalDecideBody,
    ApprovalDecideResponse,
    ApprovalDetailResponse,
    ApprovalRequestBody,
    ApprovalRequestResponse,
    PendingApprovalItem,
)
from app.services import approval_service

router = APIRouter()


@router.get("/pending", response_model=list[PendingApprovalItem])
async def list_pending_approvals(db: AsyncSession = Depends(get_db)):
    return await approval_service.list_pending(db)


@router.get("/{approval_id}", response_model=ApprovalDetailResponse)
async def get_approval(approval_id: int, db: AsyncSession = Depends(get_db)):
    return await approval_service.get_detail(db, approval_id)


@router.post(
    "/{transaction_id}/request",
    response_model=ApprovalRequestResponse,
    status_code=201,
)
async def request_exception_approval(
    transaction_id: int,
    body: ApprovalRequestBody,
    db: AsyncSession = Depends(get_db),
):
    return await approval_service.request_exception(db, transaction_id, body.reason)


@router.put("/{approval_id}/decide", response_model=ApprovalDecideResponse)
async def decide_approval(
    approval_id: int,
    body: ApprovalDecideBody,
    db: AsyncSession = Depends(get_db),
):
    return await approval_service.decide(db, approval_id, body)
