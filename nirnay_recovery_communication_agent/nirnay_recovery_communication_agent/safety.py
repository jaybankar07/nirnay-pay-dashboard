"""
Deterministic safety layer.

Runs AFTER the LLM produces text, and BEFORE that text is returned to
the caller. This is intentionally rule-based (not another LLM call) so
it is fast, auditable, and cannot itself hallucinate.

Implements the 8 checks from section 13:
    1. References the correct selected action
    2. Does not contradict compliance
    3. Does not claim recovery without evidence
    4. Does not invent financial facts
    5. Does not invent deadlines
    6. Does not contain threatening/manipulative language
    7. Does not contradict the decision
    8. Does not expose unnecessary sensitive information
"""

import re
from dataclasses import dataclass, field
from typing import List

from .enums import SelectedAction, TERMINAL_NO_ACTION_STATES
from .models import RecoveryCaseInput
from .templates import ACTION_KEYWORDS

THREATENING_PATTERNS = [
    r"\blegal action\b",
    r"\bsue you\b",
    r"\blawsuit\b",
    r"\bwill be reported\b",
    r"\bcredit score will be (damaged|destroyed|ruined)\b",
    r"\baccount will be (permanently )?(suspended|terminated|banned)\b",
    r"\bfinal notice\b",
    r"\bact now\b",
    r"\bimmediately or\b",
    r"\bpenalty\b",
    r"\bpenalties\b",
    r"\bconsequences\b",
    r"\barrest\b",
    r"\bpolice\b",
    r"\bmust pay\b",
    r"\bfailure to (pay|comply)\b",
    r"\blast chance\b",
    r"\bguarantee(d)?\b",
]

RECOVERY_SUCCESS_CLAIM_PATTERNS = [
    r"\bpayment (has been|was) (successfully )?(received|recovered|completed)\b",
    r"\bwe have received your payment\b",
    r"\bmoney has been recovered\b",
    r"\bsuccessfully (recovered|charged|collected)\b",
    r"\bthank you for your payment\b",
]

COMPLIANCE_APPROVAL_CLAIM_PATTERNS = [
    r"\bRBI[- ]?approved\b",
    r"\bcompliance[- ]?approved\b",
    r"\blegally approved\b",
]

DEADLINE_INVENTION_PATTERNS = [
    r"\bwithin \d+ (hour|hours|day|days)\b",
    r"\bby (january|february|march|april|may|june|july|august|september|"
    r"october|november|december) \d{1,2}\b",
    r"\bbefore \d{1,2}[:/]\d{2}\b",
]

CURRENCY_NUMBER_PATTERN = re.compile(
    r"(?:₹|rs\.?|inr|\$|usd)\s?([0-9][0-9,]*(?:\.[0-9]+)?)", re.IGNORECASE
)

SENSITIVE_PATTERNS = [
    r"\b\d{12,19}\b",  # raw card/account-like numbers
    r"\bcvv\b",
    r"\baadhaar\b",
    r"\bpan\s*number\b",
]


@dataclass
class SafetyReport:
    passed: bool
    violations: List[str] = field(default_factory=list)

    def add(self, violation: str):
        self.violations.append(violation)
        self.passed = False


def _normalize_amount(amount) -> str:
    if amount is None:
        return None
    # Compare using a normalized numeric string (drop trailing .0, commas)
    try:
        f = float(str(amount).replace(",", ""))
        if f == int(f):
            return str(int(f))
        return str(f)
    except (ValueError, TypeError):
        return str(amount)


def run_safety_checks(text: str, case: RecoveryCaseInput) -> SafetyReport:
    report = SafetyReport(passed=True)
    if not text or not text.strip():
        report.add("EMPTY_OUTPUT")
        return report

    lowered = text.lower()
    selected_action = SelectedAction(case.selected_action)

    # --- 1. References the correct selected action --------------------------------
    expected_keywords = ACTION_KEYWORDS.get(selected_action, [])
    if expected_keywords and not any(kw in lowered for kw in expected_keywords):
        report.add("ACTION_MISMATCH")

    # --- 2 & 7. Does not contradict compliance / the decision ----------------------
    compliance_status = (case.compliance_result or {}).get("status")
    if compliance_status == "BLOCKED" or selected_action in TERMINAL_NO_ACTION_STATES:
        # message must NOT imply an active recovery attempt is proceeding
        active_recovery_phrases = [
            "we will retry",
            "retrying your payment",
            "attempting the payment again",
            "processing your recovery",
        ]
        if any(p in lowered for p in active_recovery_phrases):
            report.add("CONTRADICTS_BLOCKED_DECISION")

    # --- 3. Does not claim recovery without evidence --------------------------------
    outcome_status = (case.recovery_outcome or {}).get("status")
    if outcome_status != "SUCCESS":
        for pattern in RECOVERY_SUCCESS_CLAIM_PATTERNS:
            if re.search(pattern, lowered):
                report.add("UNSUBSTANTIATED_RECOVERY_CLAIM")
                break

    # --- claims of compliance/RBI approval not present on input ---------------------
    if compliance_status != "APPROVED":
        for pattern in COMPLIANCE_APPROVAL_CLAIM_PATTERNS:
            if re.search(pattern, lowered):
                report.add("UNSUBSTANTIATED_COMPLIANCE_CLAIM")
                break
    else:
        # even if approved generally, never claim RBI approval unless the
        # input explicitly says so
        if "rbi" in lowered and not (case.compliance_result or {}).get(
            "rbi_approved"
        ):
            report.add("UNSUBSTANTIATED_RBI_CLAIM")

    # --- 4. Does not invent financial facts (amounts not present on input) ---------
    found_amounts = CURRENCY_NUMBER_PATTERN.findall(text)
    if found_amounts:
        expected = _normalize_amount(case.amount_at_risk)
        for amt in found_amounts:
            normalized_found = _normalize_amount(amt)
            if expected is None or normalized_found != expected:
                report.add("HALLUCINATED_AMOUNT")
                break

    # --- 5. Does not invent deadlines ------------------------------------------------
    has_supplied_deadline = bool((case.extra or {}).get("deadline"))
    if not has_supplied_deadline:
        for pattern in DEADLINE_INVENTION_PATTERNS:
            if re.search(pattern, lowered):
                report.add("INVENTED_DEADLINE")
                break

    # --- 6. Threatening / manipulative language -------------------------------------
    for pattern in THREATENING_PATTERNS:
        if re.search(pattern, lowered):
            report.add("THREATENING_LANGUAGE")
            break

    # --- 8. Unnecessary sensitive information exposure ------------------------------
    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, lowered):
            report.add("SENSITIVE_INFO_EXPOSURE")
            break

    return report
