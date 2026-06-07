from pydantic import BaseModel


class AnomalyResult(BaseModel):
    department_id: int
    department_name: str
    current_spending: float
    mean_spending: float
    z_score: float
    is_anomaly: bool
    excess_amount: float  # max(0, current - mean)


class SaasOptimizeReportResponse(BaseModel):
    subscription_id: int
    subscription_name: str
    report: str


class AnomalyExplainReportResponse(BaseModel):
    department_id: int
    department_name: str
    report: str
