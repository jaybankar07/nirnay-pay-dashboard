from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.repositories.recovery_case_repository import RecoveryCaseRepository
from app.repositories.decision_repository import DecisionRepository
from app.repositories.action_repository import ActionRepository
from app.repositories.idempotency_repository import IdempotencyRepository
from app.models.recovery_action import RecoveryAction
from app.models.recovery_outcome import RecoveryOutcome
from app.simulation.execution_simulator import BoundedExecutionSimulator
from app.services.audit_service import AuditService
from app.rules.compliance_rules import ComplianceEngine
from app.rules.stopping_rules import StoppingRulesEngine
from app.rules.recovery_rights_rules import RecoveryRightsEngine
from app.utils.enums import (
    RecoveryCaseStatus, ActionStatus, ComplianceResult,
    AuditEventType, ActorType, ActionType
)
from app.core.exceptions import (
    NotFoundError, ExecutionBlockedError, ExecutionFailedError, ComplianceBlockedError
)


from app.core.kill_switch import KillSwitchState
from app.core.invariants import FinancialInvariants
from app.core.state_machine import RecoveryStateMachine
from app.models.financial_ledger import FinancialLedgerEntry


class ExecutionService:
    def __init__(self, db: Session):
        self.db = db
        self.case_repo = RecoveryCaseRepository(db)
        self.decision_repo = DecisionRepository(db)
        self.action_repo = ActionRepository(db)
        self.idempotency_repo = IdempotencyRepository(db)
        self.audit_service = AuditService(db)

    def execute_decision(
        self,
        merchant_id: str,
        case_id: str,
        decision_id: str,
        idempotency_key: Optional[str] = None,
        endpoint: str = "/api/v1/recovery-cases/execute"
    ) -> Dict[str, Any]:
        # 0. Check Kill Switch Status
        allowed, kill_reason = KillSwitchState.is_execution_allowed(tenant_id=merchant_id)
        if not allowed:
            raise ExecutionBlockedError(kill_reason)

        # 1. Lock RecoveryCase with row-level locking (FOR UPDATE in PostgreSQL)
        case = self.case_repo.get_by_id(merchant_id, case_id, lock_for_update=True)
        if not case:
            raise NotFoundError(f"Recovery case '{case_id}' not found for merchant '{merchant_id}'.")

        # 1b. Validate Case Financial Invariants
        FinancialInvariants.validate_case_amounts(case.amount_at_risk_paise)

        # 2. Check & Reserve Idempotency Key atomically before executing action
        if idempotency_key:
            existing = self.idempotency_repo.get(merchant_id, endpoint, idempotency_key)
            if existing:
                if existing.response_code == 200:
                    return existing.response_json
                raise ExecutionBlockedError("Concurrent request is currently processing this idempotency key.")
            
            try:
                # Atomically reserve key prior to execution
                self.idempotency_repo.create(
                    merchant_id=merchant_id,
                    endpoint=endpoint,
                    idempotency_key=idempotency_key,
                    response_code=102,
                    response_json={"status": "PROCESSING"}
                )
            except IntegrityError:
                self.db.rollback()
                existing = self.idempotency_repo.get(merchant_id, endpoint, idempotency_key)
                if existing and existing.response_code == 200:
                    return existing.response_json
                raise ExecutionBlockedError("Concurrent request is currently processing this idempotency key.")

        # 3. Verify Decision belongs to case & merchant (safely handling non-UUID decision_id strings)
        import uuid
        decision = None
        if decision_id:
            try:
                valid_dec_id = str(uuid.UUID(decision_id))
                decision = self.decision_repo.get_by_id(valid_dec_id)
            except (ValueError, TypeError):
                decision = None

        if not decision:
            decision = self.decision_repo.get_latest_for_case(case_id)

        if not decision or str(decision.recovery_case_id) != str(case_id):
            raise NotFoundError(f"No valid decision found for case '{case_id}'.")

        # 4. Re-check Compliance Gate
        attempts = self.action_repo.count_attempts_for_case(case_id)
        comp_result, allowed, blocked, comp_reason = ComplianceEngine.evaluate(
            [decision.selected_action], attempts
        )
        if comp_result == ComplianceResult.BLOCKED or decision.selected_action in blocked:
            raise ExecutionBlockedError(f"Compliance check failed prior to execution: {comp_reason}")

        # 5. Re-check Stopping Rules
        should_stop, stop_reason = StoppingRulesEngine.should_stop(attempts)
        if should_stop:
            self.case_repo.update_status(case, RecoveryCaseStatus.STOPPED)
            self.audit_service.log_event(case_id, AuditEventType.CASE_STOPPED, ActorType.RULE, {"reason": stop_reason})
            raise ExecutionBlockedError(f"Execution blocked by stopping rule: {stop_reason}")

        # 6. Re-check Action executable
        if decision.selected_action == ActionType.STOP:
            raise ExecutionBlockedError("Selected action is STOP. Cannot execute payment recovery.")

        # 7. Execute bounded simulation inside DB transaction
        attempt_number = attempts + 1
        status, recovered, recovered_amount_paise, outcome_code, failure_reason = BoundedExecutionSimulator.execute_action(
            action_type=decision.selected_action,
            amount_at_risk_paise=case.amount_at_risk_paise,
            attempt_number=attempt_number
        )
        # Validate output financial invariants
        FinancialInvariants.validate_recovery_outcome(case.amount_at_risk_paise, recovered_amount_paise)

        try:
            # Create RecoveryAction
            action = RecoveryAction(
                decision_id=decision.id,
                action_type=decision.selected_action,
                attempt_number=attempt_number,
                status=status
            )
            created_action = self.action_repo.create_action(action)

            # Create RecoveryOutcome
            outcome = RecoveryOutcome(
                action_id=created_action.id,
                recovered=recovered,
                recovered_amount_paise=recovered_amount_paise,
                outcome_code=outcome_code,
                failure_reason=failure_reason
            )
            self.action_repo.create_outcome(outcome)

            # Validate State Machine Transition & Update Case Status
            new_status = RecoveryCaseStatus.RECOVERED if recovered else RecoveryCaseStatus.FAILED
            RecoveryStateMachine.validate_transition(case.status, new_status)
            self.case_repo.update_status(case, new_status)

            # Record Authoritative Financial Ledger Entry
            ledger_entry = FinancialLedgerEntry(
                tenant_id=merchant_id,
                recovery_case_id=case_id,
                execution_action_id=str(created_action.id),
                idempotency_key=idempotency_key,
                amount_at_risk_paise=case.amount_at_risk_paise,
                recovered_amount_paise=recovered_amount_paise,
                currency=getattr(case, 'currency', 'INR') or "INR",
                execution_status=status.value if hasattr(status, 'value') else str(status),
                reconciliation_status="MATCHED"
            )
            self.db.add(ledger_entry)
            self.db.flush()

            # Audit Event
            event_type = AuditEventType.ACTION_EXECUTED if status == ActionStatus.SUCCESS else AuditEventType.ACTION_FAILED
            self.audit_service.log_event(
                case_id=case_id,
                event_type=event_type,
                actor_type=ActorType.SYSTEM,
                event_data={
                    "action_id": str(created_action.id),
                    "action_type": decision.selected_action.value if hasattr(decision.selected_action, 'value') else str(decision.selected_action),
                    "status": status.value if hasattr(status, 'value') else str(status),
                    "recovered": recovered,
                    "recovered_amount_paise": recovered_amount_paise,
                    "outcome_code": outcome_code
                }
            )

            act_type_str = decision.selected_action.value if hasattr(decision.selected_action, 'value') else str(decision.selected_action)
            stat_str = status.value if hasattr(status, 'value') else str(status)
            result = {
                "action_id": str(created_action.id),
                "status": stat_str,
                "recovered": recovered,
                "recovered_amount_paise": recovered_amount_paise,
                "action_result": {
                    "action": act_type_str,
                    "status": stat_str,
                    "recovered_amount": recovered_amount_paise / 100.0,
                    "outcome_reason": failure_reason or f"Action {act_type_str} completed with status {stat_str}."
                }
            }

            # Update Idempotency Key Record with final 200 result
            if idempotency_key:
                idemp_rec = self.idempotency_repo.get(merchant_id, endpoint, idempotency_key)
                if idemp_rec:
                    idemp_rec.response_code = 200
                    idemp_rec.response_json = result
                    self.db.commit()

            return result

        except Exception as e:
            import traceback
            print(f"[EXECUTION EXCEPTION TRACEBACK]:\n{traceback.format_exc()}", flush=True)
            self.db.rollback()
            raise ExecutionFailedError(f"Execution persistence failed: {str(e)}")
