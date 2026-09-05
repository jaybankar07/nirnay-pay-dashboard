from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.repositories.recovery_case_repository import RecoveryCaseRepository
from app.repositories.decision_repository import DecisionRepository
from app.ai.agent_bridge import AgentBridge
from app.services.audit_service import AuditService
from app.utils.enums import AuditEventType, ActorType, DecisionMode
from app.core.logging import logger


class CommunicationService:
    """
    Independent service for Agent 2 (Nirnay Recovery Communication & Explanation Agent).
    Executes AFTER decision commitment.
    Communication failures or timeouts will NEVER rollback decisions or block recovery execution.
    """
    def __init__(self, db: Session):
        self.db = db
        self.case_repo = RecoveryCaseRepository(db)
        self.decision_repo = DecisionRepository(db)
        self.agent_bridge = AgentBridge()
        self.audit_service = AuditService(db)

    async def generate_explanation(
        self,
        merchant_id: str,
        case_id: str,
        decision_id: str,
        purpose: str = "MERCHANT_EXPLANATION"
    ) -> Dict[str, Any]:
        case = self.case_repo.get_by_id(merchant_id, case_id)
        decision = self.decision_repo.get_by_id(decision_id)

        if not case or not decision:
            logger.warning(f"CommunicationService: case '{case_id}' or decision '{decision_id}' not found.")
            return {
                "explanation": "Decision explanation unavailable.",
                "customer_message": "Action taken in accordance with account policy.",
                "selected_action": decision.selected_action.value if decision else "STOP"
            }

        authoritative_action = decision.selected_action.value if hasattr(decision.selected_action, "value") else str(decision.selected_action)
        scenario_str = case.scenario_type.value if hasattr(case.scenario_type, "value") else str(case.scenario_type)
        segment_str = case.customer.customer_segment.value if (case.customer and hasattr(case.customer.customer_segment, "value")) else (str(case.customer.customer_segment) if case.customer else "FIRST_TIME")
        comp_str = decision.compliance_result.value if hasattr(decision.compliance_result, "value") else str(decision.compliance_result)
        rights_str = decision.recovery_right.value if hasattr(decision.recovery_right, "value") else str(decision.recovery_right)

        comm_input = {
            "recovery_case_id": str(case.id),
            "scenario_type": scenario_str,
            "customer_segment": segment_str,
            "amount_at_risk": float(case.amount_at_risk_paise or 0) / 100.0,
            "diagnosis": case.root_cause or "unspecified_risk",
            "compliance_result": {"status": comp_str},
            "recovery_rights": {"right": rights_str},
            "selected_action": authoritative_action,  # Passed as read-only context
            "recovery_score": float(decision.recovery_score or 0.0),
            "decision_rationale": decision.ai_rationale or "Decision based on risk policy score.",
            "communication_purpose": purpose
        }

        # Call Agent 2 via AgentBridge
        comm_res, metadata = await self.agent_bridge.generate_communication_with_agent(comm_input)

        explanation = comm_res.get("explanation", f"Action {authoritative_action} authorized.")
        customer_msg = comm_res.get("customer_message", "")

        # Log audit event with agent metadata inside event_data_json
        try:
            self.audit_service.log_event(
                case_id=case.id,
                event_type=AuditEventType.DECISION_MADE,
                actor_type=ActorType.AI if decision.decision_mode == DecisionMode.AI else ActorType.RULE,
                event_data={
                    "decision_id": str(decision.id),
                    "explanation": explanation,
                    "customer_message": customer_msg,
                    "agent_name": metadata["agent_name"],
                    "fallback_used": metadata["fallback_used"],
                    "validation_status": metadata["validation_status"],
                    "latency_ms": metadata["latency_ms"],
                    "retry_count": metadata["retry_count"]
                }
            )
        except Exception as e:
            logger.warning(f"Audit log for CommunicationService failed silently: {str(e)}")

        return {
            "decision_id": str(decision.id),
            "explanation": explanation,
            "customer_message": customer_msg,
            "selected_action": authoritative_action
        }
