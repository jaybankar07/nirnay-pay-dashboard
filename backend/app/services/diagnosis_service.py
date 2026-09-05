from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.recovery_case_repository import RecoveryCaseRepository
from app.ai.agent_bridge import AgentBridge
from app.services.audit_service import AuditService
from app.utils.enums import RecoveryCaseStatus, AuditEventType, ActorType, DecisionMode
from app.core.exceptions import NotFoundError


class DiagnosisService:
    def __init__(self, db: Session):
        self.db = db
        self.case_repo = RecoveryCaseRepository(db)
        self.agent_bridge = AgentBridge()
        self.audit_service = AuditService(db)

    async def diagnose_case(
        self,
        merchant_id: str,
        case_id: str,
        support_notes: Optional[str] = None,
        customer_message: Optional[str] = None
    ) -> Dict[str, Any]:
        case = self.case_repo.get_by_id(merchant_id, case_id)
        if not case:
            raise NotFoundError(f"Recovery case '{case_id}' not found for merchant '{merchant_id}'.")

        reason_code = case.revenue_event.reason_code if case.revenue_event else None
        customer_segment = case.customer.customer_segment if case.customer else "FIRST_TIME"

        case_input = {
            "recovery_case_id": str(case.id),
            "scenario_type": case.scenario_type.value if hasattr(case.scenario_type, "value") else str(case.scenario_type),
            "amount_at_risk_paise": case.amount_at_risk_paise,
            "currency": "INR",
            "customer_segment": customer_segment,
            "reason_code": reason_code or "UNKNOWN",
            "support_notes": support_notes or "",
            "customer_message": customer_message or "",
            "successful_payment_count": case.customer.successful_payment_count if case.customer else 1,
            "failed_payment_count": case.customer.failed_payment_count if case.customer else 0,
        }

        # Run diagnosis via AgentBridge (Agent 1 + fallback safety)
        diag_res, metadata = await self.agent_bridge.diagnose_case_with_agent(case_input)

        root_cause = diag_res.get("root_cause", "unspecified_risk")
        confidence = float(diag_res.get("confidence", 0.5))
        mode_str = diag_res.get("diagnosis_mode", "AI")
        mode = DecisionMode.AI if mode_str == "AI" else DecisionMode.FALLBACK
        rationale = diag_res.get("narrative", "Diagnosis completed by Agent 1.")

        # Update case
        case.root_cause = root_cause
        case.diagnosis_confidence = confidence
        case.status = RecoveryCaseStatus.DIAGNOSED
        self.case_repo.update_status(case, RecoveryCaseStatus.DIAGNOSED)

        # Log audit event with agent invocation metadata in event_data_json
        actor = ActorType.AI if mode == DecisionMode.AI else ActorType.RULE
        self.audit_service.log_event(
            case_id=case.id,
            event_type=AuditEventType.DIAGNOSIS_COMPLETED,
            actor_type=actor,
            event_data={
                "root_cause": root_cause,
                "confidence": confidence,
                "mode": mode.value,
                "rationale": rationale,
                "agent_name": metadata["agent_name"],
                "fallback_used": metadata["fallback_used"],
                "validation_status": metadata["validation_status"],
                "latency_ms": metadata["latency_ms"],
                "retry_count": metadata["retry_count"]
            }
        )

        return {
            "case_id": str(case.id),
            "root_cause": root_cause,
            "confidence": confidence,
            "mode": mode.value,
            "rationale": rationale
        }
