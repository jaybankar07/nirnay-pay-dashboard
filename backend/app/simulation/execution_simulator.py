from typing import Tuple, Optional
from app.utils.enums import ActionType, ActionStatus, RevenueEventType


class BoundedExecutionSimulator:
    """
    Bounded Simulation Layer.
    Strictly simulates recovery actions without executing real payment transactions.
    Causally computes simulated gateway outcome based on execution parameters.
    """

    @classmethod
    def execute_action(
        cls,
        action_type: ActionType | str,
        amount_at_risk_paise: int,
        attempt_number: int = 1,
        scenario_type: Optional[RevenueEventType | str] = None,
        reason_code: Optional[str] = None,
        seed_int: Optional[int] = None,
        is_baseline: bool = False
    ) -> Tuple[ActionStatus, bool, int, str, Optional[str]]:
        """
        Simulates action execution.
        Returns: (status, recovered, recovered_amount_paise, outcome_code, failure_reason)
        """
        act_str = action_type.value if hasattr(action_type, 'value') else str(action_type)
        scen_str = scenario_type.value if hasattr(scenario_type, 'value') else str(scenario_type or "")
        reason_str = str(reason_code or "").upper()

        if act_str == "STOP":
            return (
                ActionStatus.BLOCKED,
                False,
                0,
                "CASE_STOPPED_GOVERNED",
                "Recovery explicitly stopped by policy governance."
            )
        elif act_str == "WAIT":
            return (
                ActionStatus.SUCCESS,
                False,
                0,
                "WAITING_PERIOD_INITIATED",
                "Waiting period active. Payment retry deferred to optimal window."
            )
        elif act_str == "HUMAN_REVIEW":
            return (
                ActionStatus.SUCCESS,
                False,
                0,
                "HUMAN_REVIEW_QUEUED",
                "High-value or complex policy case queued for human agent review."
            )

        if attempt_number > 3:
            return (
                ActionStatus.FAILED,
                False,
                0,
                "SIMULATED_DECLINE_MAX_ATTEMPTS",
                "Attempt failed in simulation due to max retries limit."
            )

        # Deterministic seed for reproducible simulation outcome
        if seed_int is None:
            seed_int = 42

        # Causal simulation rules based on action, scenario, reason, and attempt
        # Rule A: CHECKOUT_ABANDONMENT
        if scen_str == "CHECKOUT_ABANDONMENT":
            if act_str == "RETRY":
                # Blindly auto-charging abandoned checkout fails 100% (no authorization)
                return (
                    ActionStatus.FAILED,
                    False,
                    0,
                    "SIMULATED_DECLINE_UNAUTHORIZED",
                    "Auto-retry payment failed: Abandoned checkout requires customer authorization."
                )
            elif act_str in ["REMINDER", "WHATSAPP"]:
                # WhatsApp reminder with discount/checkout link recovers 75%
                success = (seed_int % 100) < 75
                if success:
                    return (ActionStatus.SUCCESS, True, amount_at_risk_paise, "SIMULATED_CHECKOUT_RECOVERY_SUCCESS", None)
                else:
                    return (ActionStatus.FAILED, False, 0, "SIMULATED_REMINDER_NO_RESPONSE", "Customer did not complete checkout.")

        # Rule B: OVERDUE_RECEIVABLE
        if scen_str == "OVERDUE_RECEIVABLE":
            if act_str == "RETRY":
                # Direct card charge fails on overdue corporate invoice
                return (
                    ActionStatus.FAILED,
                    False,
                    0,
                    "SIMULATED_DECLINE_INVOICE_NOT_PAYABLE_VIA_CARD",
                    "Direct card charge declined: Overdue invoice requires formal collection/notice."
                )
            elif act_str in ["ESCALATE", "REMINDER"]:
                # Escalation / Notice recovers 60%
                success = (seed_int % 100) < 60
                if success:
                    # Partial recovery model for high-value invoices (>= ₹10,000)
                    if amount_at_risk_paise >= 1000000 and attempt_number == 1:
                        partial_amount = amount_at_risk_paise // 2
                        return (ActionStatus.SUCCESS, True, partial_amount, "SIMULATED_PARTIAL_INVOICE_RECOVERY", "Partial payment received.")
                    return (ActionStatus.SUCCESS, True, amount_at_risk_paise, "SIMULATED_INVOICE_RECOVERY_SUCCESS", None)
                else:
                    return (ActionStatus.FAILED, False, 0, "SIMULATED_ESCALATION_PENDING", "Escalation notice sent, awaiting payment.")

        # Rule C: INSUFFICIENT_FUNDS
        if "INSUFFICIENT_FUNDS" in reason_str:
            if act_str == "RETRY":
                if is_baseline or attempt_number == 1:
                    # Immediate retry without giving time to add funds has low success (20%)
                    success = (seed_int % 100) < 20
                else:
                    # Retry on 2nd attempt after reminder/wait has high success (80%)
                    success = (seed_int % 100) < 80
                if success:
                    return (ActionStatus.SUCCESS, True, amount_at_risk_paise, "SIMULATED_RECOVERY_SUCCESS", None)
                else:
                    return (ActionStatus.FAILED, False, 0, "SIMULATED_DECLINE_INSUFFICIENT_FUNDS", "Declined: Insufficient funds in customer account.")
            elif act_str in ["REMINDER", "WHATSAPP"]:
                # Reminder alerts customer to top up funds -> 70% success
                success = (seed_int % 100) < 70
                if success:
                    return (ActionStatus.SUCCESS, True, amount_at_risk_paise, "SIMULATED_REMINDER_RECOVERY_SUCCESS", None)
                else:
                    return (ActionStatus.FAILED, False, 0, "SIMULATED_REMINDER_NO_ACTION", "Customer notified but account not topped up.")

        # Rule D: EXPIRED_CARD / INVALID_CARD
        if "EXPIRED" in reason_str or "CARD" in reason_str:
            if act_str == "RETRY":
                # Retry on expired card fails 100%
                return (
                    ActionStatus.FAILED,
                    False,
                    0,
                    "SIMULATED_DECLINE_EXPIRED_CARD",
                    "Declined: Card expired. Requires customer card update."
                )
            elif act_str in ["REMINDER", "WHATSAPP"]:
                # Reminder prompts card update -> 65% success
                success = (seed_int % 100) < 65
                if success:
                    return (ActionStatus.SUCCESS, True, amount_at_risk_paise, "SIMULATED_CARD_UPDATED_RECOVERY_SUCCESS", None)
                else:
                    return (ActionStatus.FAILED, False, 0, "SIMULATED_CARD_UPDATE_PENDING", "Card update link sent, awaiting customer action.")

        # Rule E: NETWORK_TIMEOUT / TECHNICAL_ERROR
        if "TIMEOUT" in reason_str or "NETWORK" in reason_str or "GATEWAY" in reason_str:
            # Immediate retry on network glitch succeeds 85%
            success = (seed_int % 100) < 85
            if success:
                return (ActionStatus.SUCCESS, True, amount_at_risk_paise, "SIMULATED_TECHNICAL_RETRY_SUCCESS", None)
            else:
                return (ActionStatus.FAILED, False, 0, "SIMULATED_GATEWAY_TIMEOUT", "Gateway timeout on retry.")

        # Default fallback for other scenarios:
        if act_str == "RETRY":
            success = (seed_int % 100) < 50
        else:
            success = (seed_int % 100) < 60

        if success:
            return (ActionStatus.SUCCESS, True, amount_at_risk_paise, "SIMULATED_RECOVERY_SUCCESS", None)
        else:
            return (ActionStatus.FAILED, False, 0, "SIMULATED_DECLINE_GENERAL", "Simulated recovery attempt declined.")
