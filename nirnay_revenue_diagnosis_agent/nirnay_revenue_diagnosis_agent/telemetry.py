"""
Structured internal telemetry (section 15).

Emits a structured record per diagnosis request. Deliberately excludes
sensitive customer/payment content (message text, decline codes, amounts)
-- it records *shape* and *outcome*, not payload.
"""
from __future__ import annotations

import logging
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger("nirnay_agent")


@dataclass
class TelemetryRecord:
    request_id: str
    recovery_case_id: Optional[str]
    scenario_type: Optional[str]
    provider: Optional[str]
    latency_ms: Optional[float] = None
    retry_count: int = 0
    diagnosis_mode: Optional[str] = None
    validation_status: str = "PENDING"
    failure_reason: Optional[str] = None
    started_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TelemetryRecorder:
    """Lightweight helper for building and emitting a TelemetryRecord for
    a single `diagnose()` call."""

    def __init__(self, recovery_case_id: Optional[str], scenario_type: Optional[str],
                 provider: Optional[str] = None):
        self.record = TelemetryRecord(
            request_id=str(uuid.uuid4()),
            recovery_case_id=recovery_case_id,
            scenario_type=scenario_type,
            provider=provider,
        )
        self._start = time.monotonic()

    def mark_retry(self) -> None:
        self.record.retry_count += 1

    def finish(self, diagnosis_mode: Optional[str], validation_status: str,
               failure_reason: Optional[str] = None) -> TelemetryRecord:
        self.record.latency_ms = round((time.monotonic() - self._start) * 1000, 3)
        self.record.diagnosis_mode = diagnosis_mode
        self.record.validation_status = validation_status
        self.record.failure_reason = failure_reason
        logger.info("nirnay_agent.diagnosis", extra={"telemetry": self.record.to_dict()})
        return self.record
