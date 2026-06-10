from fastapi import APIRouter

from app.api.v1.endpoints import (
    approvals,
    audit,
    dashboard,
    employees,
    policies,
    realtime,
    recommendations,
    reports,
    saas,
    transactions,
)

api_router = APIRouter()

api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(employees.router, prefix="/employees", tags=["employees"])
api_router.include_router(saas.router, prefix="/saas", tags=["saas"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
api_router.include_router(policies.router, prefix="/policies", tags=["policies"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(realtime.router, prefix="/realtime", tags=["realtime"])
api_router.include_router(audit.router, prefix="/audit-log", tags=["audit"])
