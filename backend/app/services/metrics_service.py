from typing import Dict, Any, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.recovery_case import RecoveryCase
from app.models.recovery_action import RecoveryAction
from app.models.recovery_outcome import RecoveryOutcome
from app.models.decision import Decision
from app.utils.enums import RecoveryCaseStatus, ComplianceResult


class MetricsService:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_summary(self, merchant_id: str) -> Dict[str, Any]:
        """
        Derives dashboard KPIs dynamically from authoritative recovery_outcomes and recovery_cases.
        """
        # Total merchant cases
        total_cases = self.db.query(RecoveryCase).filter(
            RecoveryCase.merchant_id == merchant_id
        ).count()

        # Revenue at risk
        risk_result = self.db.query(
            func.coalesce(func.sum(RecoveryCase.amount_at_risk_paise), 0)
        ).filter(
            RecoveryCase.merchant_id == merchant_id
        ).scalar()
        revenue_at_risk_paise = int(risk_result)

        # Revenue recovered
        recovered_result = self.db.query(
            func.coalesce(func.sum(RecoveryOutcome.recovered_amount_paise), 0)
        ).join(
            RecoveryAction, RecoveryOutcome.action_id == RecoveryAction.id
        ).join(
            Decision, RecoveryAction.decision_id == Decision.id
        ).join(
            RecoveryCase, Decision.recovery_case_id == RecoveryCase.id
        ).filter(
            RecoveryCase.merchant_id == merchant_id,
            RecoveryOutcome.recovered == True
        ).scalar()
        revenue_recovered_paise = int(recovered_result)

        # Recovery rate
        if revenue_at_risk_paise > 0:
            recovery_rate = round(revenue_recovered_paise / float(revenue_at_risk_paise), 4)
        else:
            recovery_rate = 0.0

        # Active cases
        active_cases = self.db.query(RecoveryCase).filter(
            RecoveryCase.merchant_id == merchant_id,
            RecoveryCase.status.in_([
                RecoveryCaseStatus.DETECTED,
                RecoveryCaseStatus.DIAGNOSED,
                RecoveryCaseStatus.IN_REVIEW,
                RecoveryCaseStatus.APPROVED
            ])
        ).count()

        # Compliance blocks
        compliance_blocks = self.db.query(RecoveryCase).filter(
            RecoveryCase.merchant_id == merchant_id,
            RecoveryCase.status == RecoveryCaseStatus.BLOCKED
        ).count()

        # Stopped cases
        stopped_cases = self.db.query(RecoveryCase).filter(
            RecoveryCase.merchant_id == merchant_id,
            RecoveryCase.status == RecoveryCaseStatus.STOPPED
        ).count()

        # Scenario breakdown
        scenario_rows = self.db.query(
            RecoveryCase.scenario_type,
            func.count(RecoveryCase.id).label("case_count"),
            func.coalesce(func.sum(RecoveryCase.amount_at_risk_paise), 0).label("at_risk_paise")
        ).filter(
            RecoveryCase.merchant_id == merchant_id
        ).group_by(RecoveryCase.scenario_type).all()

        scenario_breakdown = [
            {
                "scenario": row[0].value if hasattr(row[0], 'value') else str(row[0]),
                "amount_at_risk": int(row[2]),
                "cases": int(row[1])
            }
            for row in scenario_rows
        ]

        return {
            "revenue_at_risk_paise": revenue_at_risk_paise,
            "revenue_recovered_paise": revenue_recovered_paise,
            "active_cases": active_cases,
            "compliance_blocks": compliance_blocks,
            "stopped_cases": stopped_cases,
            "total_cases": total_cases,
            "recovery_rate": recovery_rate,
            "scenario_breakdown": scenario_breakdown,
            "performance": [],
            "data_source": "LIVE_DATABASE"
        }

