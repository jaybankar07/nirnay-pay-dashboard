import pytest
from app.ai.fallback import DeterministicFallback
from app.ai.client import AIClient
from app.utils.enums import DecisionMode, RevenueEventType, ActionType


def test_deterministic_fallback_diagnosis():
    cause, conf, mode, rationale = DeterministicFallback.get_fallback_diagnosis(
        reason_code="CARD_EXPIRED",
        scenario_type=RevenueEventType.PAYMENT_FAILURE
    )
    assert cause == "card_expired"
    assert mode == DecisionMode.FALLBACK
    assert conf == 0.70


@pytest.mark.asyncio
async def test_ai_client_fallback_on_unstructured_text_absence():
    client = AIClient(api_key="mock-key")
    cause, conf, mode, rationale = await client.diagnose(
        support_notes=None,
        customer_message=None,
        reason_code="TEMPORARY_DECLINE"
    )
    assert cause == "temporary_payment_failure"
    assert mode == DecisionMode.FALLBACK
