import pytest
from app.rules.stopping_rules import StoppingRulesEngine


def test_stopping_rules_trigger_on_max_attempts():
    should_stop, reason = StoppingRulesEngine.should_stop(current_attempt_count=4)
    assert should_stop is True
    assert "exceeded" in reason.lower()


def test_stopping_rules_explicit_stop():
    should_stop, reason = StoppingRulesEngine.should_stop(current_attempt_count=1, explicit_stop=True)
    assert should_stop is True
    assert "explicit" in reason.lower()
