from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.approval_log import ApprovalLog
    from app.models.department import Department
    from app.models.policy import AIPaymentPolicy
    from app.models.saas_usage import SaasUsage
    from app.models.transaction import Transaction


class Employee(TimestampMixin, Base):
    __tablename__ = "employee"

    employee_id: Mapped[int] = mapped_column(primary_key=True)
    employee_name: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[str] = mapped_column(String(100), nullable=False)
    department_id: Mapped[int] = mapped_column(ForeignKey("department.department_id"), nullable=False)

    department: Mapped[Department] = relationship(
        "Department", back_populates="employees", lazy="select"
    )
    saas_usages: Mapped[list[SaasUsage]] = relationship(
        "SaasUsage", back_populates="employee", lazy="select"
    )
    transactions: Mapped[list[Transaction]] = relationship(
        "Transaction", back_populates="employee", lazy="select"
    )
    policies: Mapped[list[AIPaymentPolicy]] = relationship(
        "AIPaymentPolicy", back_populates="employee", lazy="select"
    )
    approval_logs: Mapped[list[ApprovalLog]] = relationship(
        "ApprovalLog", back_populates="approver", lazy="select"
    )
