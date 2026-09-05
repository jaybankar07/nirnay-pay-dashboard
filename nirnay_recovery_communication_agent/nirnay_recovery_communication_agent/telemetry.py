"""
Observability (section 15).

Emits structured telemetry records. By default records are handed to a
simple in-memory sink / stdout logger via a callback, so this module has
no dependency on a specific logging or metrics backend.

Sensitive customer/payment content is deliberately excluded -- only
metadata is recorded.
"""

import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Callable, Optional


@dataclass
class TelemetryRecord:
    request_id: str
    recovery_case_id: str
    generation_type: str  # communication_purpose
    provider: str
    started_at: float
    latency_ms: Optional[float] = None
    retry_count: int = 0
    validation_status: str = "UNKNOWN"  # PASSED | FAILED | N/A
    fallback_used: bool = False
    failure_reason: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("started_at", None)
        return d


class Telemetry:
    def __init__(self, sink: Optional[Callable[[dict], None]] = None):
        self.sink = sink or (lambda record: None)
        self.records = []  # kept in-memory for inspection/testing

    def start(self, recovery_case_id: str, generation_type: str, provider: str) -> TelemetryRecord:
        return TelemetryRecord(
            request_id=str(uuid.uuid4()),
            recovery_case_id=recovery_case_id,
            generation_type=generation_type,
            provider=provider,
            started_at=time.monotonic(),
        )

    def finish(
        self,
        record: TelemetryRecord,
        validation_status: str,
        fallback_used: bool,
        retry_count: int,
        failure_reason: Optional[str] = None,
    ) -> None:
        record.latency_ms = round((time.monotonic() - record.started_at) * 1000, 3)
        record.validation_status = validation_status
        record.fallback_used = fallback_used
        record.retry_count = retry_count
        record.failure_reason = failure_reason
        self.records.append(record)
        self.sink(record.to_dict())
