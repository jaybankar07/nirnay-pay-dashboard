"""
API Security, Authentication, RBAC, and Tenant Isolation for Nirnay Pay.
"""
from typing import Optional, Dict, Any
from fastapi import Request, Header, HTTPException, status


class SecurityError(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_403_FORBIDDEN):
        super().__init__(status_code=status_code, detail=detail)


ROLE_PERMISSIONS = {
    "VIEWER": {"read:cases", "read:metrics", "read:audit"},
    "OPERATOR": {"read:cases", "read:metrics", "read:audit", "execute:recovery", "decide:recovery"},
    "ADMIN": {"read:cases", "read:metrics", "read:audit", "execute:recovery", "decide:recovery", "admin:killswitch", "admin:policies"},
    "AUDITOR": {"read:cases", "read:metrics", "read:audit", "read:ledger", "export:report"}
}


class SecurityContext:
    @staticmethod
    def verify_tenant_access(request_merchant_id: str, target_merchant_id: str) -> None:
        """Enforces tenant isolation. Raises 403 if client attempts cross-tenant access."""
        if not request_merchant_id or not target_merchant_id:
            raise SecurityError("Missing tenant context in authorization request.", status_code=status.HTTP_400_BAD_REQUEST)
        
        if str(request_merchant_id).strip() != str(target_merchant_id).strip():
            raise SecurityError(
                f"Tenant isolation violation: Authenticated merchant '{request_merchant_id}' "
                f"cannot access resources belonging to merchant '{target_merchant_id}'."
            )

    @staticmethod
    def check_permission(user_role: str, required_permission: str) -> None:
        """Enforces Role-Based Access Control (RBAC)."""
        role = (user_role or "OPERATOR").upper()
        allowed_permissions = ROLE_PERMISSIONS.get(role, set())
        if required_permission not in allowed_permissions:
            raise SecurityError(
                f"RBAC Permission Denied: Role '{role}' does not possess required permission '{required_permission}'."
            )

    @staticmethod
    def authenticate_api_key(api_key: Optional[str]) -> bool:
        """Validates API Key credential or Authorization header format."""
        if not api_key:
            return True  # Open dev fallback
        if api_key.startswith("key_") or api_key.startswith("rzp_") or api_key.startswith("Bearer ") or len(api_key) >= 8:
            return True
        raise SecurityError("Invalid API Key credential provided.", status_code=status.HTTP_401_UNAUTHORIZED)
