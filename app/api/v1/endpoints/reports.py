from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.saas_subscription import SaasSubscription
from app.models.saas_usage import SaasUsage
from app.schemas.report import (
    AnomalyExplainReportResponse,
    AnomalyResult,
    SaasOptimizeReportResponse,
)
from app.services import ai_report, anomaly_detection

router = APIRouter()


@router.get("/anomaly", response_model=list[AnomalyResult])
async def get_anomaly_report(
    anomaly_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    results = await anomaly_detection.detect(db)
    if anomaly_only:
        return [r for r in results if r.is_anomaly]
    return results


@router.post(
    "/saas-optimize/{subscription_id}",
    response_model=SaasOptimizeReportResponse,
)
async def saas_optimize_report(
    subscription_id: int,
    db: AsyncSession = Depends(get_db),
):
    sub = await db.get(SaasSubscription, subscription_id)
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription {subscription_id} not found",
        )

    ghost_count = (
        await db.execute(
            select(SaasUsage).where(
                SaasUsage.subscription_id == subscription_id,
                SaasUsage.is_ghost_account == True,  # noqa: E712
            )
        )
    )
    ghost_account_count = len(ghost_count.scalars().all())

    report_text = await ai_report.generate_saas_optimize_report(
        subscription_id=sub.subscription_id,
        subscription_name=sub.subscription_name,
        provider=sub.provider,
        monthly_fee=float(sub.monthly_fee),
        total_seats=sub.total_seats,
        used_seats=sub.used_seats,
        wasted_amount=float(sub.wasted_amount),
        risk_level=sub.risk_level.value,
        ghost_account_count=ghost_account_count,
    )

    return SaasOptimizeReportResponse(
        subscription_id=sub.subscription_id,
        subscription_name=sub.subscription_name,
        report=report_text,
    )


@router.post(
    "/anomaly-explain/{department_id}",
    response_model=AnomalyExplainReportResponse,
)
async def anomaly_explain_report(
    department_id: int,
    db: AsyncSession = Depends(get_db),
):
    all_results = await anomaly_detection.detect(db)

    dept_result: AnomalyResult | None = next(
        (r for r in all_results if r.department_id == department_id), None
    )
    if dept_result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department {department_id} not found",
        )

    report_text = await ai_report.generate_anomaly_explain_report(dept_result)

    return AnomalyExplainReportResponse(
        department_id=dept_result.department_id,
        department_name=dept_result.department_name,
        report=report_text,
    )
