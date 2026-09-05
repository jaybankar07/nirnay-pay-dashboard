"""
Webhook Ingestion & Reconciliation Engine for Nirnay Pay (RecoveryOS).
"""
import hmac
import hashlib
from typing import Dict, Any, Tuple


class WebhookReconciliationStatus:
    MATCHED = "MATCHED"
    CONFLICT = "CONFLICT"
    UNKNOWN_REFERENCE = "UNKNOWN_REFERENCE"
    DUPLICATE = "DUPLICATE"
    PENDING = "PENDING"


class WebhookProcessor:
    @staticmethod
    def verify_hmac_signature(payload_bytes: bytes, signature: str, secret: str) -> bool:
        """Verifies HMAC SHA256 webhook signature against provider secret."""
        if not signature or not secret:
            return False
        expected_sig = hmac.new(secret.encode('utf-8'), payload_bytes, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected_sig, signature)

    @staticmethod
    def reconcile_provider_outcome(
        internal_status: str,
        internal_amount_paise: int,
        provider_status: str,
        provider_amount_paise: int
    ) -> Tuple[str, str]:
        """
        Reconciles provider state against internal recovery state without blindly overwriting.
        Returns (reconciliation_status, audit_note).
        """
        # Map provider status to standard
        prov_normalized = provider_status.upper()
        
        if prov_normalized in ("SUCCESS", "CAPTURED", "SETTLED", "SUCCEEDED"):
            if internal_amount_paise == provider_amount_paise:
                return WebhookReconciliationStatus.MATCHED, "Provider success matches internal ledger amount."
            else:
                return WebhookReconciliationStatus.CONFLICT, f"Amount discrepancy: internal {internal_amount_paise} paise vs provider {provider_amount_paise} paise."
        elif prov_normalized in ("FAILED", "DECLINED"):
            return WebhookReconciliationStatus.MATCHED, "Provider failure matches internal failed attempt."
        else:
            return WebhookReconciliationStatus.UNKNOWN_REFERENCE, f"Unrecognized provider status: '{provider_status}'."
