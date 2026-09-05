import hashlib
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.batch_run import BatchRun
from app.models.recovery_case import RecoveryCase
from app.repositories.batch_repository import BatchRepository
from app.repositories.recovery_case_repository import RecoveryCaseRepository
from app.simulation.execution_simulator import BoundedExecutionSimulator
from app.utils.enums import BatchStrategy, ActionType
from app.core.exceptions import NotFoundError, ValidationError


class BatchSimulationService:
    def __init__(self, db: Session):
        self.db = db
        self.batch_repo = BatchRepository(db)
        self.case_repo = RecoveryCaseRepository(db)

    def run_batch_simulation(
        self,
        merchant_id: str,
        strategy: BatchStrategy,
        case_ids: List[str]
    ) -> Dict[str, Any]:
        if not case_ids:
            raise ValidationError("Batch simulation requires at least one case ID.")

        total_cases = len(case_ids)
        total_at_risk_paise = 0
        baseline_recovered_paise = 0
        nirnay_recovered_paise = 0
        compliance_blocks = 0
        stopped_cases = 0

        act_count = 0
        wait_count = 0
        escalate_count = 0
        stop_count = 0
        successful_interventions = 0
        unsuccessful_interventions = 0

        action_diff_count = 0
        outcome_diff_count = 0

        cases_in_db = self.db.query(RecoveryCase).filter(
            RecoveryCase.merchant_id == merchant_id,
            RecoveryCase.id.in_(case_ids)
        ).all()
        case_map = {str(c.id): c for c in cases_in_db}

        for case_id in case_ids:
            case = case_map.get(str(case_id))
            if not case:
                continue

            amount_paise = case.amount_at_risk_paise
            total_at_risk_paise += amount_paise

            # Reproducible pseudo-random seed based on case ID for execution simulator
            seed_hash = hashlib.md5(f"{case.id}_{merchant_id}".encode()).hexdigest()
            seed_int = int(seed_hash[:8], 16)

            scen_str = case.scenario_type.value if hasattr(case.scenario_type, "value") else str(case.scenario_type)
            reason_str = str(case.root_cause or "")
            is_blocked = (case.status.value == "BLOCKED" if hasattr(case.status, "value") else str(case.status) == "BLOCKED")

            # -----------------------------------------------------------------
            # 1. BASELINE STRATEGY: Blind payment gateway RETRY without governance
            # -----------------------------------------------------------------
            baseline_action = ActionType.RETRY
            status_base, rec_base, amount_base, code_base, reason_base = BoundedExecutionSimulator.execute_action(
                action_type=baseline_action,
                amount_at_risk_paise=amount_paise,
                attempt_number=1,
                scenario_type=scen_str,
                reason_code=reason_str,
                seed_int=seed_int,
                is_baseline=True
            )
            if rec_base:
                baseline_recovered_paise += amount_base

            # -----------------------------------------------------------------
            # 2. NIRNAY PAY STRATEGY: Governed pipeline with policy & diagnosis
            # -----------------------------------------------------------------
            if is_blocked:
                compliance_blocks += 1
                stop_count += 1
                stopped_cases += 1
                nirnay_action = ActionType.STOP
                rec_nirnay = False
                amount_nirnay = 0
            else:
                # Determine action based on policy and scenario rules
                if amount_paise > 500000 or scen_str == "OVERDUE_RECEIVABLE":
                    nirnay_action = ActionType.ESCALATE
                    escalate_count += 1
                elif scen_str == "CHECKOUT_ABANDONMENT":
                    nirnay_action = ActionType.REMINDER
                    act_count += 1
                elif "EXPIRED" in reason_str.upper() or "CARD" in reason_str.upper():
                    nirnay_action = ActionType.REMINDER
                    act_count += 1
                elif "INSUFFICIENT_FUNDS" in reason_str.upper():
                    nirnay_action = ActionType.REMINDER
                    act_count += 1
                elif "TIMEOUT" in reason_str.upper() or "NETWORK" in reason_str.upper():
                    nirnay_action = ActionType.RETRY
                    act_count += 1
                else:
                    nirnay_action = ActionType.RETRY
                    act_count += 1

                status_nirnay, rec_nirnay, amount_nirnay, code_nirnay, reason_nirnay = BoundedExecutionSimulator.execute_action(
                    action_type=nirnay_action,
                    amount_at_risk_paise=amount_paise,
                    attempt_number=1,
                    scenario_type=scen_str,
                    reason_code=reason_str,
                    seed_int=seed_int,
                    is_baseline=False
                )
                if rec_nirnay:
                    nirnay_recovered_paise += amount_nirnay
                    successful_interventions += 1
                else:
                    unsuccessful_interventions += 1

            if nirnay_action != baseline_action:
                action_diff_count += 1
            if amount_nirnay != amount_base:
                outcome_diff_count += 1

        recovered_paise = nirnay_recovered_paise if strategy == BatchStrategy.NIRNAY_PAY else baseline_recovered_paise
        recovery_rate = round(recovered_paise / float(total_at_risk_paise), 4) if total_at_risk_paise > 0 else 0.0

        baseline_rate = round(baseline_recovered_paise / float(total_at_risk_paise), 4) if total_at_risk_paise > 0 else 0.0
        nirnay_rate = round(nirnay_recovered_paise / float(total_at_risk_paise), 4) if total_at_risk_paise > 0 else 0.0

        # Honest incremental calculation (can be positive, zero, or negative)
        incremental_recovered_paise = nirnay_recovered_paise - baseline_recovered_paise

        batch_run = BatchRun(
            merchant_id=merchant_id,
            strategy=strategy,
            total_cases=total_cases,
            total_at_risk_paise=total_at_risk_paise,
            recovered_paise=recovered_paise,
            recovery_rate=recovery_rate,
            compliance_blocks=compliance_blocks
        )
        saved = self.batch_repo.create(batch_run)

        return {
            "batch_run_id": str(saved.id),
            "strategy": strategy.value,
            "total_cases": total_cases,
            "total_at_risk_paise": total_at_risk_paise,
            "recovered_paise": recovered_paise,
            "baseline_recovered_paise": baseline_recovered_paise,
            "nirnay_recovered_paise": nirnay_recovered_paise,
            "incremental_recovered_paise": incremental_recovered_paise,
            "recovery_rate": recovery_rate,
            "baseline_recovery_rate": baseline_rate,
            "nirnay_recovery_rate": nirnay_rate,
            "compliance_blocks": compliance_blocks,
            "stopped_cases": stopped_cases,
            "action_difference_count": action_diff_count,
            "outcome_difference_count": outcome_diff_count,
            "act_count": act_count,
            "wait_count": wait_count,
            "escalate_count": escalate_count,
            "stop_count": stop_count,
            "successful_interventions": successful_interventions,
            "unsuccessful_interventions": unsuccessful_interventions,
            "data_source": "SIMULATED / SYNTHETIC EVALUATION"
        }

