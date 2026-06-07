import json
from datetime import date, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.audit_log import AuditLog
from app.schemas.audit import AuditLogItem, AuditVerifyResponse
from app.services import audit_service

router = APIRouter()


@router.get("", response_model=list[AuditLogItem])
async def list_audit_logs(
    event_type: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AuditLog).order_by(AuditLog.audit_id.desc()).limit(limit)

    if event_type is not None:
        stmt = stmt.where(AuditLog.event_type == event_type)
    if start_date is not None:
        stmt = stmt.where(
            AuditLog.created_at >= datetime.combine(start_date, datetime.min.time())
        )
    if end_date is not None:
        stmt = stmt.where(
            AuditLog.created_at <= datetime.combine(end_date, datetime.max.time())
        )

    rows = (await db.execute(stmt)).scalars().all()

    return [
        AuditLogItem(
            audit_id=log.audit_id,
            event_type=log.event_type,
            event_data=json.loads(log.event_data),
            current_hash=log.current_hash,
            created_at=log.created_at,
        )
        for log in rows
    ]


@router.get("/verify", response_model=AuditVerifyResponse)
async def verify_audit_chain(db: AsyncSession = Depends(get_db)):
    is_valid, total, invalid_id = await audit_service.verify_chain(db)
    return AuditVerifyResponse(
        is_valid=is_valid,
        total_records=total,
        invalid_audit_id=invalid_id,
    )
