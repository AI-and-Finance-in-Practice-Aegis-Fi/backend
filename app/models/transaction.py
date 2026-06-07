from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.approval_log import ApprovalLog
    from app.models.employee import Employee


class Transaction(TimestampMixin, Base):
    __tablename__ = "transaction"

    transaction_id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employee.employee_id"), nullable=False)
    merchant_name: Mapped[str] = mapped_column(String(200), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    user_input_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ai_predicted_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_approved: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    ai_risk_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    ai_risk_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    payment_time: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

    employee: Mapped[Employee] = relationship(
        "Employee", back_populates="transactions", lazy="select"
    )
    approval_logs: Mapped[list[ApprovalLog]] = relationship(
        "ApprovalLog", back_populates="transaction", lazy="select"
    )
