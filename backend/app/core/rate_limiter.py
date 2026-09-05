"""
Rate Limiting, Payload Boundary, and Request Safety Module for Nirnay Pay (RecoveryOS).
Enforces sliding window rate limits, payload size constraints, and pagination bounds.
"""
import time
import threading
from typing import Dict, Tuple, List
from fastapi import HTTPException, status, Request


class RateLimiter:
    _requests: Dict[str, List[float]] = {}
    _lock = threading.Lock()
    MAX_REQUESTS_PER_MINUTE = 120
    WINDOW_SECONDS = 60

    @classmethod
    def check_rate_limit(cls, identifier: str) -> None:
        """Enforces rate limit sliding window per identifier (tenant or IP)."""
        now = time.time()
        window_start = now - cls.WINDOW_SECONDS

        with cls._lock:
            if identifier not in cls._requests:
                cls._requests[identifier] = []
            
            # Prune old timestamps
            cls._requests[identifier] = [ts for ts in cls._requests[identifier] if ts > window_start]
            
            if len(cls._requests[identifier]) >= cls.MAX_REQUESTS_PER_MINUTE:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded ({cls.MAX_REQUESTS_PER_MINUTE} requests/min) for identifier '{identifier}'."
                )

            cls._requests[identifier].append(now)

    @classmethod
    def validate_pagination_limit(cls, limit: int, max_allowed: int = 100) -> int:
        """Validates pagination bounds to prevent resource exhaustion."""
        if limit <= 0:
            return 10
        if limit > max_allowed:
            return max_allowed
        return limit
