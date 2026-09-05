"""
Financial Invariants Validation Module for Nirnay Pay (RecoveryOS).
Enforces exact integer paise arithmetic and financial integrity rules.
"""
from typing import Dict, Any, Tuple


class FinancialInvariantError(ValueError):
    """Exception raised when a financial invariant is violated."""
    pass


class FinancialInvariants:
    @staticmethod
    def validate_case_amounts(amount_at_risk_paise: int) -> None:
        """Validates case initial at-risk amount."""
        if not isinstance(amount_at_risk_paise, int):
            raise FinancialInvariantError(f"Amount at risk must be an integer (paise), got {type(amount_at_risk_paise).__name__}")
        if amount_at_risk_paise < 0:
            raise FinancialInvariantError(f"Amount at risk cannot be negative: {amount_at_risk_paise} paise")

    @staticmethod
    def validate_recovery_outcome(amount_at_risk_paise: int, recovered_amount_paise: int) -> None:
        """Validates recovery outcome amount against at-risk amount."""
        if not isinstance(recovered_amount_paise, int):
            raise FinancialInvariantError(f"Recovered amount must be an integer (paise), got {type(recovered_amount_paise).__name__}")
        if recovered_amount_paise < 0:
            raise FinancialInvariantError(f"Recovered amount cannot be negative: {recovered_amount_paise} paise")
        if recovered_amount_paise > amount_at_risk_paise:
            raise FinancialInvariantError(
                f"Recovered amount ({recovered_amount_paise} paise) exceeds amount at risk ({amount_at_risk_paise} paise)"
            )

    @staticmethod
    def compute_incremental_recovery(nirnay_paise: int, baseline_paise: int) -> int:
        """Computes incremental recovery. Incremental MAY be negative (Nirnay lose case)."""
        if not isinstance(nirnay_paise, int) or not isinstance(baseline_paise, int):
            raise FinancialInvariantError("Batch recovery amounts must be integers (paise)")
        if nirnay_paise < 0 or baseline_paise < 0:
            raise FinancialInvariantError("Individual strategy recovered amounts cannot be negative")
        return nirnay_paise - baseline_paise
