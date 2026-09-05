import pytest
from app.services.recovery_score_service import RecoveryScoreService


def test_recovery_score_formula(db_session, seeded_merchant, seeded_case):
    service = RecoveryScoreService(db_session)
    candidates = [
        {"action": "RETRY", "probability_of_recovery": 0.8, "channel_cost_paise": 0, "compliance_penalty_paise": 0},
        {"action": "REMINDER", "probability_of_recovery": 0.5, "channel_cost_paise": 100, "compliance_penalty_paise": 0}
    ]

    res = service.calculate_scores(seeded_merchant.id, seeded_case.id, candidates)
    scores = res["scores"]
    assert len(scores) == 2
    # Score = P(recovery) * amount_at_risk_paise - channel_cost - compliance_penalty
    # For RETRY: 0.8 * 49900 - 0 = 39920.0
    retry_score = next(s["score"] for s in scores if s["action"] == "RETRY")
    assert retry_score == 39920.0
    assert res["recommended_action"] == "RETRY"
