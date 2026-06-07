from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditLogItem(BaseModel):
    audit_id: int
    event_type: str
    event_data: Any  # JSON-parsed dict in responses
    current_hash: str
    created_at: datetime


class AuditVerifyResponse(BaseModel):
    is_valid: bool
    total_records: int
    invalid_audit_id: int | None
