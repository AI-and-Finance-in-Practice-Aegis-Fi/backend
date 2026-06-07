from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.transaction import Transaction


class ApprovalLog(TimestampMixin, Base):
    __tablename__ = "approval_log"

    approval_id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("transaction.transaction_id"), nullable=False
    )
    # nullable: None = pending (not yet assigned)
    approver_employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("employee.employee_id"), nullable=True
    )
    # nullable: None = pending decision
    approval_result: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    approval_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # nullable: None = not yet decided
    approval_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    transaction: Mapped[Transaction] = relationship(
        "Transaction", back_populates="approval_logs", lazy="select"
    )
    approver: Mapped[Employee | None] = relationship(
        "Employee", back_populates="approval_logs", lazy="select"
    )
