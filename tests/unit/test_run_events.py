from __future__ import annotations

from datetime import UTC, datetime

from harness.run_events import (
    HITLDecision,
    RunEvent,
    RunEventType,
    RunPhase,
    TestStatus,
    apply_event_to_snapshot,
    sanitize_event_metadata,
)


def test_run_event_serializes_to_json_safe_payload_with_iso_timestamp() -> None:
    event = RunEvent(
        event_id="evt-1",
        run_id="run-1",
        event_type=RunEventType.TASK_STARTED,
        timestamp=datetime(2026, 7, 15, 9, 0, 1, tzinfo=UTC),
        phase=RunPhase.RUNNING,
        summary="Task started",
        metadata={"requirement": "implement feature"},
    )

    payload = event.to_dict()

    assert payload == {
        "event_id": "evt-1",
        "run_id": "run-1",
        "event_type": "task_started",
        "timestamp": "2026-07-15T09:00:01Z",
        "round_index": None,
        "phase": "running",
        "summary": "Task started",
        "tool_name": None,
        "tool_status": None,
        "test_status": None,
        "hitl_request_id": None,
        "hitl_decision": None,
        "stop_reason": None,
        "metadata": {"requirement": "implement feature"},
    }


def test_event_snapshot_transitions_do_not_create_idle_running_conflict() -> None:
    snapshot = apply_event_to_snapshot(None, None)

    assert snapshot["phase"] == "idle"
    assert snapshot["status"] == "Not started"
    assert snapshot["stop_reason"] is None

    snapshot = apply_event_to_snapshot(
        snapshot,
        RunEvent(
            event_id="evt-1",
            run_id="run-1",
            event_type=RunEventType.TASK_STARTED,
            phase=RunPhase.RUNNING,
            summary="Task started",
        ),
    )
    assert snapshot["phase"] == "running"
    assert snapshot["status"] == "Running"
    assert snapshot["stop_reason"] is None

    snapshot = apply_event_to_snapshot(
        snapshot,
        RunEvent(
            event_id="evt-2",
            run_id="run-1",
            event_type=RunEventType.HITL_REQUESTED,
            phase=RunPhase.AWAITING_APPROVAL,
            hitl_request_id="hitl-1",
            summary="Approval required",
        ),
    )
    assert snapshot["phase"] == "awaiting_approval"
    assert snapshot["status"] == "Awaiting approval"

    snapshot = apply_event_to_snapshot(
        snapshot,
        RunEvent(
            event_id="evt-3",
            run_id="run-1",
            event_type=RunEventType.HITL_RESOLVED,
            phase=RunPhase.RUNNING,
            hitl_request_id="hitl-1",
            hitl_decision=HITLDecision.DENIED,
            summary="Denied",
        ),
    )
    assert snapshot["phase"] == "running"
    assert snapshot["status"] == "Running"
    assert snapshot["stop_reason"] is None


def test_tests_and_finish_events_update_snapshot_semantics() -> None:
    snapshot = apply_event_to_snapshot(
        None,
        RunEvent(
            event_id="evt-1",
            run_id="run-1",
            event_type=RunEventType.TESTS_STARTED,
            phase=RunPhase.TESTING,
            test_status=TestStatus.RUNNING,
            summary="Running tests",
        ),
    )

    assert snapshot["phase"] == "testing"
    assert snapshot["status"] == "Running tests"
    assert snapshot["test_status"] == "running"

    snapshot = apply_event_to_snapshot(
        snapshot,
        RunEvent(
            event_id="evt-2",
            run_id="run-1",
            event_type=RunEventType.RUN_FINISHED,
            phase=RunPhase.COMPLETED,
            stop_reason="PASS",
            summary="Done",
        ),
    )

    assert snapshot["phase"] == "completed"
    assert snapshot["status"] == "Completed"
    assert snapshot["stop_reason"] == "PASS"


def test_run_event_metadata_sanitizer_redacts_secrets_headers_env_and_paths() -> None:
    metadata = {
        "api_key": "sk-test-secret",
        "headers": {"Authorization": "Bearer secret"},
        "env": "DEEPSEEK_API_KEY=secret",
        "cmd": "type C:\\Users\\student\\project\\.env",
        "nested": [{"target_directory": "C:\\Users\\student\\repo"}],
    }

    sanitized = sanitize_event_metadata(metadata)
    rendered = str(sanitized)

    assert "sk-test-secret" not in rendered
    assert "Bearer secret" not in rendered
    assert "DEEPSEEK_API_KEY=secret" not in rendered
    assert "C:\\Users\\student" not in rendered
    assert sanitized["api_key"] == "[redacted]"
    assert sanitized["headers"]["Authorization"] == "[redacted]"

