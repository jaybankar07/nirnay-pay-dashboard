"""
Independent Raw-Record Financial Oracle & Reconciliation Service for Nirnay Pay (RecoveryOS).
Directly computes financial sums from immutable database tables to verify zero synthetic uplift.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.recovery_case import RecoveryCase
from app.models.decision import Decision
from app.models.recovery_action import RecoveryAction
from app.models.recovery_outcome import RecoveryOutcome
from app.models.financial_ledger import FinancialLedgerEntry
from app.core.invariants import FinancialInvariants


class IndependentFinancialOracle:
    def __init__(self, db: Session):
        self.db = db

    def trace_case_causal_chain(self, case_id: str) -> Dict[str, Any]:
        """Traces complete case-level causal recovery chain:
        Case -> Decision -> Action -> Execution -> Outcome -> Ledger.
        """
        case = self.db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
        if not case:
            return {"error": f"Case '{case_id}' not found."}

        decisions = self.db.query(Decision).filter(Decision.recovery_case_id == case_id).all()
        decisions_data = []
        for dec in decisions:
            actions = self.db.query(RecoveryAction).filter(RecoveryAction.decision_id == dec.id).all()
            actions_data = []
            for act in actions:
                outcome = self.db.query(RecoveryOutcome).filter(RecoveryOutcome.action_id == act.id).first()
                actions_data.append({
                    "action_id": act.id,
                    "action_type": act.action_type.value if hasattr(act.action_type, 'value') else str(act.action_type),
                    "attempt_number": act.attempt_number,
                    "status": act.status.value if hasattr(act.status, 'value') else str(act.status),
                    "outcome": {
                        "recovered": outcome.recovered if outcome else False,
                        "recovered_amount_paise": outcome.recovered_amount_paise if outcome else 0,
                        "outcome_code": outcome.outcome_code if outcome else None,
                    } if outcome else None
                })

            decisions_data.append({
                "decision_id": dec.id,
                "selected_action": dec.selected_action.value if hasattr(dec.selected_action, 'value') else str(dec.selected_action),
                "decision_mode": dec.decision_mode.value if hasattr(dec.decision_mode, 'value') else str(dec.decision_mode),
                "actions": actions_data
            })

        ledger_entries = self.db.query(FinancialLedgerEntry).filter(FinancialLedgerEntry.recovery_case_id == case_id).all()

        return {
            "case_id": case.id,
            "merchant_id": case.merchant_id,
            "status": case.status.value if hasattr(case.status, 'value') else str(case.status),
            "amount_at_risk_paise": case.amount_at_risk_paise,
            "scenario_type": case.scenario_type.value if hasattr(case.scenario_type, 'value') else str(case.scenario_type),
            "decisions": decisions_data,
            "ledger_entries": [e.to_dict() for e in ledger_entries],
            "total_ledger_recovered_paise": sum(e.recovered_amount_paise for e in ledger_entries)
        }

    def reconcile_tenant_financials(self, tenant_id: str) -> Dict[str, Any]:
        """Computes raw SQL database sums for tenant and verifies ledger reconciliation."""
        entries = self.db.query(FinancialLedgerEntry).filter(FinancialLedgerEntry.tenant_id == tenant_id).all()

        total_at_risk = sum(e.amount_at_risk_paise for e in entries)
        total_recovered = sum(e.recovered_amount_paise for e in entries)

        # Check reconciliation status counts
        matched_count = sum(1 for e in entries if e.reconciliation_status == "MATCHED")
        discrepancy_count = sum(1 for e in entries if e.reconciliation_status == "DISCREPANCY")
        unreconciled_count = sum(1 for e in entries if e.reconciliation_status in ["UNRECONCILED", "RECONCILIATION_REQUIRED"])

        return {
            "tenant_id": tenant_id,
            "total_ledger_entries": len(entries),
            "total_at_risk_paise": total_at_risk,
            "total_recovered_paise": total_recovered,
            "total_recovered_inr": total_recovered / 100.0,
            "reconciliation_breakdown": {
                "MATCHED": matched_count,
                "DISCREPANCY": discrepancy_count,
                "UNRECONCILED": unreconciled_count
            },
            "is_financially_reconciled": (discrepancy_count == 0)
        }
