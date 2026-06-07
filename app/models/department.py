from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.policy import AIPaymentPolicy
    from app.models.saas_subscription import SaasSubscription


class Department(TimestampMixin, Base):
    __tablename__ = "department"

    department_id: Mapped[int] = mapped_column(primary_key=True)
    department_name: Mapped[str] = mapped_column(String(100), nullable=False)
    monthly_budget_limit: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    current_spending: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)

    employees: Mapped[list[Employee]] = relationship(
        "Employee", back_populates="department", lazy="select"
    )
    saas_subscriptions: Mapped[list[SaasSubscription]] = relationship(
        "SaasSubscription", back_populates="department", lazy="select"
    )
    policies: Mapped[list[AIPaymentPolicy]] = relationship(
        "AIPaymentPolicy", back_populates="department", lazy="select"
    )
