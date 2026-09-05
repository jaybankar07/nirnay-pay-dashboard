"""
Input validation for the Nirnay Revenue Diagnosis Agent (section 2B).

Validation is intentionally strict and side-effect free: it never repairs
or infers corrupted financial data, it only accepts well-formed input or
raises a structured InputValidationError describing exactly what is
wrong.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .enums import ScenarioType
from .exceptions import InputValidationError
from .models import RecoveryCaseInput, is_valid_currency

_DECLINE_CODE_RE = re.compile(r"^[A-Za-z0-9_\-\.]{1,64}$")
_MAX_STRING_LEN = 5000
_MAX_LIST_LEN = 500


def _require_dict(raw: Any) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        raise InputValidationError(
            "Input must be a structured object (dict).", field="__root__"
        )
    return raw


def _check_string(raw: Dict[str, Any], key: str, required: bool = False,
                   max_len: int = _MAX_STRING_LEN) -> Optional[str]:
    if key not in raw or raw[key] is None:
        if required:
            raise InputValidationError(f"Missing required field: {key}.", field=key)
        return None
    value = raw[key]
    if not isinstance(value, str):
        raise InputValidationError(f"{key} must be a string.", field=key)
    if required and value.strip() == "":
        raise InputValidationError(f"{key} must not be empty.", field=key)
    if len(value) > max_len:
        raise InputValidationError(f"{key} exceeds maximum length.", field=key)
    return value


def _check_non_negative_number(raw: Dict[str, Any], key: str) -> Optional[float]:
    if key not in raw or raw[key] is None:
        return None
    value = raw[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputValidationError(f"{key} must be a number.", field=key)
    if value < 0:
        raise InputValidationError(f"{key} must not be negative.", field=key)
    return float(value)


def _check_non_negative_int(raw: Dict[str, Any], key: str) -> Optional[int]:
    if key not in raw or raw[key] is None:
        return None
    value = raw[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise InputValidationError(f"{key} must be an integer.", field=key)
    if value < 0:
        raise InputValidationError(f"{key} must not be negative.", field=key)
    return value


def _check_dict(raw: Dict[str, Any], key: str) -> Optional[Dict[str, Any]]:
    if key not in raw or raw[key] is None:
        return None
    value = raw[key]
    if not isinstance(value, dict):
        raise InputValidationError(f"{key} must be an object.", field=key)
    return value


def _check_list_of_str(raw: Dict[str, Any], key: str) -> Optional[List[str]]:
    if key not in raw or raw[key] is None:
        return None
    value = raw[key]
    if not isinstance(value, list):
        raise InputValidationError(f"{key} must be a list.", field=key)
    if len(value) > _MAX_LIST_LEN:
        raise InputValidationError(f"{key} exceeds maximum length.", field=key)
    for item in value:
        if not isinstance(item, str):
            raise InputValidationError(f"{key} must be a list of strings.", field=key)
    return value


def _check_list_of_dict(raw: Dict[str, Any], key: str) -> Optional[List[Dict[str, Any]]]:
    if key not in raw or raw[key] is None:
        return None
    value = raw[key]
    if not isinstance(value, list):
        raise InputValidationError(f"{key} must be a list.", field=key)
    if len(value) > _MAX_LIST_LEN:
        raise InputValidationError(f"{key} exceeds maximum length.", field=key)
    for item in value:
        if not isinstance(item, dict):
            raise InputValidationError(
                f"{key} must be a list of objects.", field=key
            )
    return value


def validate_input(raw: Dict[str, Any]) -> RecoveryCaseInput:
    """Validate a raw dict against the RecoveryCaseInput contract.

    Raises InputValidationError on the first violation found. On success,
    returns a fully-typed RecoveryCaseInput. Never infers or repairs
    invalid values -- invalid input is always rejected, not coerced.
    """
    raw = _require_dict(raw)

    recovery_case_id = _check_string(raw, "recovery_case_id", required=True, max_len=256)

    scenario_type_raw = _check_string(raw, "scenario_type", required=True, max_len=64)
    try:
        scenario_type = ScenarioType(scenario_type_raw)
    except ValueError:
        raise InputValidationError(
            "Unsupported scenario_type.", field="scenario_type"
        )

    amount_at_risk = _check_non_negative_number(raw, "amount_at_risk")

    currency = _check_string(raw, "currency", max_len=8)
    if currency is not None and not is_valid_currency(currency):
        raise InputValidationError(
            "currency must be a 3-letter uppercase ISO 4217 code (e.g. USD).",
            field="currency",
        )

    customer_segment = _check_string(raw, "customer_segment", max_len=128)

    customer_tenure = raw.get("customer_tenure")
    if customer_tenure is not None:
        if isinstance(customer_tenure, bool) or not isinstance(
            customer_tenure, (int, float)
        ):
            raise InputValidationError(
                "customer_tenure must be a number.", field="customer_tenure"
            )
        if customer_tenure < 0:
            raise InputValidationError(
                "customer_tenure must not be negative.", field="customer_tenure"
            )

    customer_lifetime_value = _check_non_negative_number(raw, "customer_lifetime_value")

    successful_payment_count = _check_non_negative_int(raw, "successful_payment_count")
    failed_payment_count = _check_non_negative_int(raw, "failed_payment_count")

    payment_signals = _check_dict(raw, "payment_signals")

    decline_code = _check_string(raw, "decline_code", max_len=64)
    if decline_code is not None and not _DECLINE_CODE_RE.match(decline_code):
        raise InputValidationError(
            "decline_code is malformed.", field="decline_code"
        )

    failure_reason = _check_string(raw, "failure_reason", max_len=1000)

    subscription_info = _check_dict(raw, "subscription_info")
    checkout_info = _check_dict(raw, "checkout_info")
    receivable_info = _check_dict(raw, "receivable_info")

    previous_recovery_attempts = _check_list_of_dict(raw, "previous_recovery_attempts")
    previous_outcomes = _check_list_of_str(raw, "previous_outcomes")

    customer_messages = _check_list_of_str(raw, "customer_messages")

    event_metadata = _check_dict(raw, "event_metadata")

    return RecoveryCaseInput(
        recovery_case_id=recovery_case_id,
        scenario_type=scenario_type.value,
        amount_at_risk=amount_at_risk,
        currency=currency,
        customer_segment=customer_segment,
        customer_tenure=customer_tenure,
        customer_lifetime_value=customer_lifetime_value,
        successful_payment_count=successful_payment_count,
        failed_payment_count=failed_payment_count,
        payment_signals=payment_signals,
        decline_code=decline_code,
        failure_reason=failure_reason,
        subscription_info=subscription_info,
        checkout_info=checkout_info,
        receivable_info=receivable_info,
        previous_recovery_attempts=previous_recovery_attempts,
        previous_outcomes=previous_outcomes,
        customer_messages=customer_messages,
        event_metadata=event_metadata,
    )
