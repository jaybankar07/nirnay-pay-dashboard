import pytest
from app.rules.recovery_rights_rules import RecoveryRightsEngine
from app.utils.enums import CustomerSegment, RecoveryRightTreatment


def test_recovery_rights_default_demo_policy():
    treatment, reason, is_fallback = RecoveryRightsEngine.determine_treatment(
        CustomerSegment.FIRST_TIME,
        {"FIRST_TIME": "RETRY", "LOYAL": "GRACE_PERIOD"}
    )
    assert treatment == RecoveryRightTreatment.RETRY
    assert not is_fallback

    loyal_treatment, _, _ = RecoveryRightsEngine.determine_treatment(
        CustomerSegment.LOYAL,
        {"FIRST_TIME": "RETRY", "LOYAL": "GRACE_PERIOD"}
    )
    assert loyal_treatment == RecoveryRightTreatment.GRACE_PERIOD


def test_recovery_rights_missing_policy_safe_fallback():
    # SAFE FALLBACK: Missing policy MUST fallback to HUMAN_REVIEW (never RETRY!)
    treatment, reason, is_fallback = RecoveryRightsEngine.determine_treatment(
        CustomerSegment.FIRST_TIME,
        policy_rules=None
    )
    assert treatment == RecoveryRightTreatment.HUMAN_REVIEW
    assert is_fallback
    assert "No merchant policy found" in reason


def test_recovery_rights_malformed_json_fallback():
    treatment, reason, is_fallback = RecoveryRightsEngine.determine_treatment(
        CustomerSegment.LOYAL,
        policy_rules="{invalid_json: true"
    )
    assert treatment == RecoveryRightTreatment.HUMAN_REVIEW
    assert is_fallback
    assert "malformed" in reason.lower()


def test_recovery_rights_invalid_action_fallback():
    treatment, reason, is_fallback = RecoveryRightsEngine.determine_treatment(
        CustomerSegment.PREMIUM,
        policy_rules={"PREMIUM": "INVALID_ACTION_NAME"}
    )
    assert treatment == RecoveryRightTreatment.HUMAN_REVIEW
    assert is_fallback
    assert "invalid" in reason.lower()
