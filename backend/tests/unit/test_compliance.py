import pytest
from app.rules.compliance_rules import ComplianceEngine
from app.utils.enums import ComplianceResult, ActionType


def test_compliance_approved_within_limits():
    result, allowed, blocked, reason = ComplianceEngine.evaluate(
        [ActionType.RETRY, ActionType.REMINDER],
        previous_attempts_count=1
    )
    assert result == ComplianceResult.APPROVED
    assert len(allowed) == 2


def test_compliance_blocked_exceeds_max_attempts():
    result, allowed, blocked, reason = ComplianceEngine.evaluate(
        [ActionType.RETRY],
        previous_attempts_count=3
    )
    assert result == ComplianceResult.BLOCKED
    assert len(allowed) == 0
    assert "limit" in reason.lower()
