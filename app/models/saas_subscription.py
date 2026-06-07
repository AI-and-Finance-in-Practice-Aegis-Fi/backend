from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.saas_usage import SaasUsage

import enum


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class SaasSubscription(TimestampMixin, Base):
    __tablename__ = "saas_subscription"

    subscription_id: Mapped[int] = mapped_column(primary_key=True)
    subscription_name: Mapped[str] = mapped_column(String(200), nullable=False)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    monthly_fee: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    total_seats: Mapped[int] = mapped_column(nullable=False)
    used_seats: Mapped[int] = mapped_column(nullable=False, default=0)
    wasted_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel, name="risk_level_enum"), nullable=False, default=RiskLevel.LOW
    )
    renewal_date: Mapped[Date] = mapped_column(Date, nullable=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("department.department_id"), nullable=False)

    department: Mapped[Department] = relationship(
        "Department", back_populates="saas_subscriptions", lazy="select"
    )
    saas_usages: Mapped[list[SaasUsage]] = relationship(
        "SaasUsage", back_populates="subscription", lazy="select"
    )
