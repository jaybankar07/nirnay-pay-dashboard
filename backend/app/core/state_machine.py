"""
Explicit Recovery State Machine for Nirnay Pay (RecoveryOS).
Enforces valid state transitions and rejects corrupt lifecycle mutations.
"""
from typing import Set, Dict, Tuple
from app.utils.enums import RecoveryCaseStatus


class InvalidStateTransitionError(ValueError):
    """Exception raised when an illegal state transition is attempted."""
    pass


class RecoveryStateMachine:
    # Allowed transitions map
    _ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
        "OPEN": {"DETECTED", "DIAGNOSED", "GOVERNED", "DECIDED", "APPROVED", "IN_REVIEW", "EXECUTED", "AUTHORIZED", "EXECUTING", "RECOVERED", "FAILED", "BLOCKED", "STOPPED", "ESCALATED", "UNKNOWN", "RECONCILIATION_REQUIRED"},
        "DETECTED": {"DIAGNOSED", "GOVERNED", "IN_REVIEW", "APPROVED", "DECIDED", "BLOCKED", "STOPPED", "EXECUTING", "EXECUTED", "RECOVERED", "FAILED"},
        "DIAGNOSED": {"GOVERNED", "DECIDED", "IN_REVIEW", "APPROVED", "BLOCKED", "STOPPED", "EXECUTING", "EXECUTED", "RECOVERED", "FAILED"},

        "GOVERNED": {"DECIDED", "APPROVED", "AUTHORIZED", "BLOCKED", "STOPPED", "ESCALATED"},
        "DECIDED": {"APPROVED", "AUTHORIZED", "EXECUTING", "EXECUTED", "RECOVERED", "FAILED", "BLOCKED", "STOPPED", "ESCALATED", "UNKNOWN"},
        "APPROVED": {"AUTHORIZED", "EXECUTING", "EXECUTED", "RECOVERED", "FAILED", "BLOCKED", "STOPPED", "ESCALATED", "UNKNOWN"},
        "IN_REVIEW": {"APPROVED", "DECIDED", "AUTHORIZED", "BLOCKED", "STOPPED"},
        "AUTHORIZED": {"EXECUTING", "EXECUTED", "RECOVERED", "FAILED", "BLOCKED", "STOPPED", "UNKNOWN"},
        "EXECUTING": {"EXECUTED", "RECOVERED", "FAILED", "BLOCKED", "STOPPED", "ESCALATED", "UNKNOWN", "RECONCILIATION_REQUIRED"},
        "EXECUTED": {"RECOVERED", "FAILED", "BLOCKED", "STOPPED", "UNKNOWN", "RECONCILIATION_REQUIRED"},
        "FAILED": {"AUTHORIZED", "EXECUTING", "RECOVERED", "FAILED", "STOPPED", "ESCALATED", "RECONCILIATION_REQUIRED"},
        "UNKNOWN": {"RECONCILIATION_REQUIRED", "RECOVERED", "FAILED"},
        "RECONCILIATION_REQUIRED": {"RECOVERED", "FAILED"},
        "RECOVERED": set(),  # Terminal success state
        "BLOCKED": set(),    # Terminal governance state
        "STOPPED": set(),    # Terminal attempt-limit state
        "ESCALATED": set(),  # Terminal human escalation state
        "EXPIRED": set(),
        "ABANDONED": set()
    }

    @classmethod
    def validate_transition(cls, current_status: str, new_status: str) -> None:
        """Validates transition from current_status to new_status."""
        curr = current_status.value if hasattr(current_status, 'value') else str(current_status)
        nxt = new_status.value if hasattr(new_status, 'value') else str(new_status)

        if curr == nxt:
            return  # Idempotent state assertion

        allowed_next = cls._ALLOWED_TRANSITIONS.get(curr, set())
        if nxt not in allowed_next:
            raise InvalidStateTransitionError(
                f"Illegal recovery state transition: '{curr}' -> '{nxt}'. "
                f"Allowed transitions from '{curr}': {sorted(list(allowed_next))}"
            )
