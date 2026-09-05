from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
    revenue_at_risk_paise: int
    revenue_recovered_paise: int
    active_cases: int
    compliance_blocks: int
    stopped_cases: int
    total_cases: int
    recovery_rate: float
