import json
from typing import Optional, Dict, Any, Tuple
from app.utils.enums import CustomerSegment, RecoveryRightTreatment


DEFAULT_DEMO_POLICY = {
    CustomerSegment.FIRST_TIME.value: RecoveryRightTreatment.RETRY.value,
    CustomerSegment.LOYAL.value: RecoveryRightTreatment.GRACE_PERIOD.value,
    CustomerSegment.PREMIUM.value: RecoveryRightTreatment.SOFT_REMINDER.value,
    CustomerSegment.HABITUAL_NON_PAYER.value: RecoveryRightTreatment.ESCALATE.value,
}


class RecoveryRightsEngine:
    @classmethod
    def determine_treatment(
        cls,
        customer_segment: CustomerSegment,
        policy_rules: Optional[Dict[str, Any] | str] = None
    ) -> Tuple[RecoveryRightTreatment, str, bool]:
        """
        Determines customer recovery treatment.
        Returns: (RecoveryRightTreatment, reason_message, is_fallback)

        SAFE FALLBACK GUARANTEE:
        If policy is missing, malformed, or invalid, returns HUMAN_REVIEW / STOP.
        RETRY is NEVER automatically authorized without a valid policy!
        """
        if policy_rules is None:
            # Safe Fallback when policy is missing
            return (
                RecoveryRightTreatment.HUMAN_REVIEW,
                "No merchant policy found. Defaulting to safe fallback (HUMAN_REVIEW).",
                True
            )

        rules_dict = {}
        if isinstance(policy_rules, str):
            try:
                rules_dict = json.loads(policy_rules)
            except Exception:
                return (
                    RecoveryRightTreatment.HUMAN_REVIEW,
                    "Merchant policy JSON malformed. Safe fallback (HUMAN_REVIEW) applied.",
                    True
                )
        elif isinstance(policy_rules, dict):
            rules_dict = policy_rules
        else:
            return (
                RecoveryRightTreatment.HUMAN_REVIEW,
                "Invalid policy rules type. Safe fallback (HUMAN_REVIEW) applied.",
                True
            )

        segment_key = customer_segment.value if isinstance(customer_segment, CustomerSegment) else str(customer_segment)

        # Check configured policy rules
        if segment_key in rules_dict:
            raw_action = rules_dict[segment_key]
            try:
                treatment = RecoveryRightTreatment(raw_action)
                return (
                    treatment,
                    f"Treatment {treatment.value} applied from merchant policy for segment {segment_key}.",
                    False
                )
            except ValueError:
                return (
                    RecoveryRightTreatment.HUMAN_REVIEW,
                    f"Configured action '{raw_action}' is invalid. Safe fallback (HUMAN_REVIEW) applied.",
                    True
                )

        # Safe fallback if segment is not defined in valid policy rules
        return (
            RecoveryRightTreatment.HUMAN_REVIEW,
            f"Segment '{segment_key}' not specified in merchant policy. Safe fallback (HUMAN_REVIEW) applied.",
            True
        )
