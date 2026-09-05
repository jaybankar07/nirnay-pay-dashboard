from typing import Tuple
from app.utils.enums import ActionType


class StoppingRulesEngine:
    MAX_ATTEMPT_LIMIT = 4

    @classmethod
    def should_stop(
        cls,
        current_attempt_count: int,
        diminishing_return_flag: bool = False,
        explicit_stop: bool = False
    ) -> Tuple[bool, str]:
        if explicit_stop:
            return True, "Explicit stop rule triggered."
        if current_attempt_count >= cls.MAX_ATTEMPT_LIMIT:
            return True, f"Maximum contact attempt limit ({cls.MAX_ATTEMPT_LIMIT}) exceeded."
        if diminishing_return_flag:
            return True, "Diminishing return threshold reached."
        return False, "Case may continue recovery."
