from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class RunEventType(StrEnum):
    TASK_STARTED = "task_started"
    ROUND_STARTED = "round_started"
    MODEL_RESPONSE = "model_response"
    TOOL_REQUESTED = "tool_requested"
    TOOL_COMPLETED = "tool_completed"
    TESTS_STARTED = "tests_started"
    TESTS_COMPLETED = "tests_completed"
    HITL_REQUESTED = "hitl_requested"
    HITL_RESOLVED = "hitl_resolved"
    RUN_FINISHED = "run_finished"


class RunPhase(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    TESTING = "testing"
    COMPLETED = "completed"
    FAILED = "failed"


class TestStatus(StrEnum):
    NOT_STARTED = "not_started"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"


class HITLDecision(StrEnum):
    APPROVED = "approved"
    DENIED = "denied"


_SENSITIVE_NAME_RE = re.compile(
    r"(api[_-]?key|authorization|token|secret|password|path|cwd|dir|directory|file)",
    re.IGNORECASE,
)
_HIGH_CONFIDENCE_SECRET_RE = re.compile(
    r"(sk-[A-Za-z0-9_-]+|AKIA[0-9A-Z]{16}|BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY)"
)
_SENSITIVE_CONTENT_RE = re.compile(
    r"(api[_-]?key|authorization|token|secret|password)\s*[:=]\s*\S+",
    re.IGNORECASE,
)
_WINDOWS_USER_PATH_RE = re.compile(r"C:\\Users\\\S+", re.IGNORECASE)
_ENV_FILE_RE = re.compile(r"\S*\.env\S*", re.IGNORECASE)


@dataclass(frozen=True)
class RunEvent:
    event_id: str
    run_id: str
    event_type: RunEventType
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    round_index: int | None = None
    phase: RunPhase | None = None
    summary: str = ""
    tool_name: str | None = None
    tool_status: str | None = None
    test_status: TestStatus | None = None
    hitl_request_id: str | None = None
    hitl_decision: HITLDecision | None = None
    stop_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "run_id": self.run_id,
            "event_type": self.event_type.value,
            "timestamp": _format_timestamp(self.timestamp),
            "round_index": self.round_index,
            "phase": self.phase.value if self.phase is not None else None,
            "summary": self.summary,
            "tool_name": self.tool_name,
            "tool_status": self.tool_status,
            "test_status": self.test_status.value if self.test_status is not None else None,
            "hitl_request_id": self.hitl_request_id,
            "hitl_decision": (
                self.hitl_decision.value if self.hitl_decision is not None else None
            ),
            "stop_reason": self.stop_reason,
            "metadata": sanitize_event_metadata(self.metadata),
        }


def sanitize_event_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    return {str(name): _sanitize_value(str(name), value) for name, value in metadata.items()}


def apply_event_to_snapshot(
    snapshot: dict[str, Any] | None,
    event: RunEvent | None,
) -> dict[str, Any]:
    current = _initial_snapshot() if snapshot is None else dict(snapshot)
    if event is None:
        return current

    if event.phase is not None:
        current["phase"] = event.phase.value
    if event.round_index is not None:
        current["round_index"] = event.round_index
    if event.test_status is not None:
        current["test_status"] = event.test_status.value
    if event.hitl_request_id is not None:
        current["hitl_request_id"] = event.hitl_request_id
    if event.hitl_decision is not None:
        current["hitl_decision"] = event.hitl_decision.value
    if event.stop_reason is not None:
        current["stop_reason"] = event.stop_reason
    current["status"] = _status_for_phase(str(current["phase"]))
    return current


def _initial_snapshot() -> dict[str, Any]:
    return {
        "phase": RunPhase.IDLE.value,
        "status": "Not started",
        "round_index": 0,
        "test_status": None,
        "hitl_request_id": None,
        "hitl_decision": None,
        "stop_reason": None,
    }


def _status_for_phase(phase: str) -> str:
    return {
        RunPhase.IDLE.value: "Not started",
        RunPhase.RUNNING.value: "Running",
        RunPhase.AWAITING_APPROVAL.value: "Awaiting approval",
        RunPhase.TESTING.value: "Running tests",
        RunPhase.COMPLETED.value: "Completed",
        RunPhase.FAILED.value: "Failed",
    }.get(phase, "Not available")


def _format_timestamp(timestamp: datetime) -> str:
    normalized = timestamp
    if normalized.tzinfo is None:
        normalized = normalized.replace(tzinfo=UTC)
    normalized = normalized.astimezone(UTC)
    return normalized.isoformat().replace("+00:00", "Z")


def _sanitize_value(name: str, value: Any) -> Any:
    if _SENSITIVE_NAME_RE.search(name):
        return "[redacted]"
    if isinstance(value, str):
        return _sanitize_string(value)
    if isinstance(value, dict):
        return {str(key): _sanitize_value(str(key), item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_value(name, item) for item in value]
    return value


def _sanitize_string(value: str) -> str:
    redacted = _HIGH_CONFIDENCE_SECRET_RE.sub("[redacted]", value)
    redacted = _SENSITIVE_CONTENT_RE.sub(
        lambda match: f"{match.group(1)}=[redacted]",
        redacted,
    )
    redacted = _WINDOWS_USER_PATH_RE.sub("[redacted]", redacted)
    redacted = _ENV_FILE_RE.sub("[redacted]", redacted)
    return redacted

