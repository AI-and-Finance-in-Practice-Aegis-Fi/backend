from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.saas_subscription import SaasSubscription


class SaasUsage(TimestampMixin, Base):
    __tablename__ = "saas_usage"

    usage_id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employee.employee_id"), nullable=False)
    subscription_id: Mapped[int] = mapped_column(
        ForeignKey("saas_subscription.subscription_id"), nullable=False
    )
    last_login_date: Mapped[Date] = mapped_column(Date, nullable=True)
    monthly_usage_count: Mapped[int] = mapped_column(nullable=False, default=0)
    is_ghost_account: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    employee: Mapped[Employee] = relationship(
        "Employee", back_populates="saas_usages", lazy="select"
    )
    subscription: Mapped[SaasSubscription] = relationship(
        "SaasSubscription", back_populates="saas_usages", lazy="select"
    )
