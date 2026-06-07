from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.employee import Employee


class AIPaymentPolicy(TimestampMixin, Base):
    __tablename__ = "ai_payment_policy"

    policy_id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("employee.employee_id"), nullable=True
    )
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("department.department_id"), nullable=True
    )
    restricted_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    single_payment_limit: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    employee: Mapped[Employee | None] = relationship(
        "Employee", back_populates="policies", lazy="select"
    )
    department: Mapped[Department | None] = relationship(
        "Department", back_populates="policies", lazy="select"
    )
