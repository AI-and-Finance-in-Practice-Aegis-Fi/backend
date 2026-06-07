"""
SHA-256 hash-chained audit log.

Each record's current_hash = SHA-256(event_data_json + prev_hash + timestamp),
making any post-hoc tampering detectable by verify_chain().
"""
import hashlib
import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


def _sha256(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


async def record(
    session: AsyncSession,
    event_type: str,
    event_data_dict: dict,
) -> AuditLog:
    result = await session.execute(
        select(AuditLog.current_hash)
        .order_by(AuditLog.audit_id.desc())
        .limit(1)
    )
    prev_hash: str = result.scalar() or "0" * 64

    timestamp = datetime.now(timezone.utc)
    event_data_json = json.dumps(event_data_dict, ensure_ascii=False, sort_keys=True)
    current_hash = _sha256(event_data_json + prev_hash + timestamp.isoformat())

    log = AuditLog(
        event_type=event_type,
        event_data=event_data_json,
        prev_hash=prev_hash,
        current_hash=current_hash,
        created_at=timestamp,
    )
    session.add(log)
    return log


async def verify_chain(session: AsyncSession) -> tuple[bool, int, int | None]:
    rows = (
        await session.execute(select(AuditLog).order_by(AuditLog.audit_id))
    ).scalars().all()

    total = len(rows)
    prev_hash = "0" * 64

    for log in rows:
        if log.prev_hash != prev_hash:
            return False, total, log.audit_id

        expected = _sha256(log.event_data + log.prev_hash + log.created_at.isoformat())
        if log.current_hash != expected:
            return False, total, log.audit_id

        prev_hash = log.current_hash

    return True, total, None
