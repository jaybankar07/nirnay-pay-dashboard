"""
Synthetic Evaluation Dataset Generator for Nirnay Pay Track 03.
Generates 100 reproducible cases with a strict 70/30 DEVELOPMENT vs HELD_OUT split.
"""
import random
from typing import List, Tuple
from app.evaluation.models import (
    EvaluationCase,
    GroundTruth,
    DatasetSplit,
    ScenarioType
)

DEFAULT_MERCHANT_ID = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"

def generate_synthetic_dataset(total_cases: int = 100, seed: int = 42) -> List[EvaluationCase]:
    """
    Generates a fixed, reproducible synthetic dataset of evaluation cases.
    Exact 70% DEVELOPMENT and 30% HELD_OUT split.
    """
    rng = random.Random(seed)
    cases: List[EvaluationCase] = []
    
    # 70 Dev, 30 Held Out
    dev_count = int(total_cases * 0.70)
    
    scenarios = [
        ScenarioType.PAYMENT_FAILURE,
        ScenarioType.CHECKOUT_ABANDONMENT,
        ScenarioType.SUBSCRIPTION_FAILURE,
        ScenarioType.OVERDUE_RECEIVABLE
    ]
    
    payment_reasons = ["INSUFFICIENT_FUNDS", "EXPIRED_CARD", "GATEWAY_TIMEOUT", "INVALID_CVV"]
    checkout_reasons = ["GATEWAY_ERROR", "OTP_TIMEOUT", "CART_ABANDONED"]
    subscription_reasons = ["MANDATE_EXPIRED", "CARD_EXPIRED", "RENEWAL_DECLINED"]
    receivable_reasons = ["INVOICE_OVERDUE_15D", "INVOICE_OVERDUE_60D", "DISPUTE_RAISED"]

    for i in range(1, total_cases + 1):
        split = DatasetSplit.DEVELOPMENT if i <= dev_count else DatasetSplit.HELD_OUT
        scenario = scenarios[(i - 1) % len(scenarios)]
        case_id = f"eval-case-{i:03d}"
        cust_id = f"cust-eval-{i:03d}"
        
        amount_paise = rng.choice([50000, 120000, 250000, 500000, 1000000, 2500000])
        failed_count = rng.choice([1, 2, 3, 4])
        success_count = rng.choice([0, 1, 5, 12])
        segment = rng.choice(["HIGH_VAL", "STANDARD", "NEW_USER"])
        tenure = rng.choice([15, 60, 180, 365])
        
        # Determine Ground Truth based on scenario & reason
        if scenario == ScenarioType.PAYMENT_FAILURE:
            reason = payment_reasons[i % len(payment_reasons)]
            if reason in ["GATEWAY_TIMEOUT", "INSUFFICIENT_FUNDS"]:
                gt = GroundTruth(
                    recovery_opportunity=True,
                    effective_actions=["RETRY"],
                    prohibited_actions=[],
                    max_recoverable_amount_paise=amount_paise,
                    wasted_cost_paise=500
                )
            elif reason == "EXPIRED_CARD":
                gt = GroundTruth(
                    recovery_opportunity=True,
                    effective_actions=["RETRY"],
                    prohibited_actions=[],
                    max_recoverable_amount_paise=amount_paise,
                    wasted_cost_paise=500
                )
            else:  # INVALID_CVV
                gt = GroundTruth(
                    recovery_opportunity=False,
                    effective_actions=["STOP"],
                    prohibited_actions=["RETRY"],
                    max_recoverable_amount_paise=0,
                    wasted_cost_paise=1000,
                    failure_reason="Invalid credentials cannot be retried"
                )
        elif scenario == ScenarioType.CHECKOUT_ABANDONMENT:
            reason = checkout_reasons[i % len(checkout_reasons)]
            if reason in ["GATEWAY_ERROR", "OTP_TIMEOUT"]:
                gt = GroundTruth(
                    recovery_opportunity=True,
                    effective_actions=["RETRY"],
                    prohibited_actions=[],
                    max_recoverable_amount_paise=amount_paise,
                    wasted_cost_paise=300
                )
            else:  # CART_ABANDONED
                gt = GroundTruth(
                    recovery_opportunity=True,
                    effective_actions=["RETRY"],
                    prohibited_actions=[],
                    max_recoverable_amount_paise=int(amount_paise * 0.90),
                    wasted_cost_paise=500
                )
        elif scenario == ScenarioType.SUBSCRIPTION_FAILURE:
            reason = subscription_reasons[i % len(subscription_reasons)]
            if reason in ["CARD_EXPIRED", "RENEWAL_DECLINED"]:
                gt = GroundTruth(
                    recovery_opportunity=True,
                    effective_actions=["RETRY"],
                    prohibited_actions=[],
                    max_recoverable_amount_paise=amount_paise,
                    wasted_cost_paise=500
                )
            else:  # MANDATE_EXPIRED
                gt = GroundTruth(
                    recovery_opportunity=False,
                    effective_actions=["ESCALATE"],
                    prohibited_actions=["RETRY"],
                    max_recoverable_amount_paise=0,
                    wasted_cost_paise=1000,
                    failure_reason="Mandate expired requires re-authorization"
                )
        else:  # OVERDUE_RECEIVABLE
            reason = receivable_reasons[i % len(receivable_reasons)]
            if reason == "INVOICE_OVERDUE_15D":
                gt = GroundTruth(
                    recovery_opportunity=True,
                    effective_actions=["RETRY"],
                    prohibited_actions=[],
                    max_recoverable_amount_paise=amount_paise,
                    wasted_cost_paise=500
                )
            elif reason == "INVOICE_OVERDUE_60D":
                gt = GroundTruth(
                    recovery_opportunity=True,
                    effective_actions=["ESCALATE"],
                    prohibited_actions=["RETRY"],
                    max_recoverable_amount_paise=int(amount_paise * 0.60),
                    wasted_cost_paise=1500
                )
            else:  # DISPUTE_RAISED
                gt = GroundTruth(
                    recovery_opportunity=False,
                    effective_actions=["STOP"],
                    prohibited_actions=["RETRY"],
                    max_recoverable_amount_paise=0,
                    wasted_cost_paise=2000,
                    failure_reason="Active commercial dispute"
                )
        
        # Add compliance boundary cases
        if failed_count >= 3:
            gt.effective_actions = ["STOP"]
            gt.recovery_opportunity = False
            gt.failure_reason = "Max compliance attempts reached"
            
        case = EvaluationCase(
            case_id=case_id,
            merchant_id=DEFAULT_MERCHANT_ID,
            customer_id=cust_id,
            split=split,
            scenario_type=scenario,
            amount_at_risk_paise=amount_paise,
            failed_payment_count=failed_count,
            successful_payment_count=success_count,
            customer_segment=segment,
            tenure_days=tenure,
            reason_code=reason,
            unstructured_signals={
                "error_code": reason,
                "customer_tier": segment,
                "days_since_failure": (i * 3) % 45
            },
            ground_truth=gt
        )
        cases.append(case)
        
    return cases

def get_split_datasets(total_cases: int = 100, seed: int = 42) -> Tuple[List[EvaluationCase], List[EvaluationCase]]:
    all_cases = generate_synthetic_dataset(total_cases, seed)
    dev_cases = [c for c in all_cases if c.split == DatasetSplit.DEVELOPMENT]
    held_out_cases = [c for c in all_cases if c.split == DatasetSplit.HELD_OUT]
    return dev_cases, held_out_cases
