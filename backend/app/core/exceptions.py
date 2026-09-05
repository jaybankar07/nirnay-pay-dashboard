from typing import Any, Dict, Optional


class NirnayPayException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(NirnayPayException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("VALIDATION_ERROR", message, 422, details)


class NotFoundError(NirnayPayException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("NOT_FOUND", message, 404, details)


class DuplicateResourceError(NirnayPayException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__("DUPLICATE_RESOURCE", message, 409, details)


class ComplianceBlockedError(NirnayPayException):
    def __init__(self, message: str = "Recovery action was blocked by compliance rules.", details: Optional[Dict[str, Any]] = None):
        super().__init__("COMPLIANCE_BLOCKED", message, 403, details)


class StoppingRuleBlockedError(NirnayPayException):
    def __init__(self, message: str = "Recovery action was blocked by stopping rules.", details: Optional[Dict[str, Any]] = None):
        super().__init__("STOPPING_RULE_BLOCKED", message, 403, details)


class AIUnavailableError(NirnayPayException):
    def __init__(self, message: str = "LLM service unavailable.", details: Optional[Dict[str, Any]] = None):
        super().__init__("AI_UNAVAILABLE", message, 503, details)


class AIInvalidOutputError(NirnayPayException):
    def __init__(self, message: str = "LLM output invalid.", details: Optional[Dict[str, Any]] = None):
        super().__init__("AI_INVALID_OUTPUT", message, 502, details)


class ExecutionFailedError(NirnayPayException):
    def __init__(self, message: str = "Simulation execution failed.", details: Optional[Dict[str, Any]] = None):
        super().__init__("EXECUTION_FAILED", message, 500, details)


class ExecutionBlockedError(NirnayPayException):
    def __init__(self, message: str = "The selected action is not executable.", details: Optional[Dict[str, Any]] = None):
        super().__init__("EXECUTION_BLOCKED", message, 403, details)


class DatabaseError(NirnayPayException):
    def __init__(self, message: str = "Database operation failed.", details: Optional[Dict[str, Any]] = None):
        super().__init__("DATABASE_ERROR", message, 500, details)


class InternalError(NirnayPayException):
    def __init__(self, message: str = "An unexpected internal error occurred.", details: Optional[Dict[str, Any]] = None):
        super().__init__("INTERNAL_ERROR", message, 500, details)
