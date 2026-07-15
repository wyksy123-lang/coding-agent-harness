from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from harness.run_events import RunEvent, RunEventType, RunPhase
from webui.app import create_app
from webui.state import WebUIState


def test_webui_state_starts_idle_without_running_stop_reason() -> None:
    state = WebUIState(mode="live", run_id="run-1")

    snapshot = state.snapshot()

    assert snapshot["mode"] == "live"
    assert snapshot["phase"] == "idle"
    assert snapshot["status"] == "Not started"
    assert snapshot["stop_reason"] is None
    assert snapshot["timeline"] == []
    assert snapshot["pending_hitl"] == []


def test_webui_state_publish_updates_snapshot_and_timeline_in_order() -> None:
    state = WebUIState(mode="live", run_id="run-1")

    state.publish(
        RunEvent(
            event_id="evt-1",
            run_id="run-1",
            event_type=RunEventType.TASK_STARTED,
            phase=RunPhase.RUNNING,
            summary="Started",
        )
    )
    state.publish(
        RunEvent(
            event_id="evt-2",
            run_id="run-1",
            event_type=RunEventType.RUN_FINISHED,
            phase=RunPhase.COMPLETED,
            stop_reason="PASS",
            summary="Passed",
        )
    )

    snapshot = state.snapshot()

    assert snapshot["phase"] == "completed"
    assert snapshot["status"] == "Completed"
    assert snapshot["stop_reason"] == "PASS"
    assert [event["event_id"] for event in snapshot["timeline"]] == ["evt-1", "evt-2"]


def test_websocket_sends_snapshot_first_then_incremental_event() -> None:
    state = WebUIState(mode="live", run_id="run-1")
    state.publish(
        RunEvent(
            event_id="evt-1",
            run_id="run-1",
            event_type=RunEventType.TASK_STARTED,
            phase=RunPhase.RUNNING,
            summary="Started",
        )
    )
    client = TestClient(create_app(state=state, mode="live"))
    executor = ThreadPoolExecutor(max_workers=1)

    try:
        with client.websocket_connect("/ws") as websocket:
            first = websocket.receive_json()
            future = executor.submit(websocket.receive_json)
            state.publish(
                RunEvent(
                    event_id="evt-2",
                    run_id="run-1",
                    event_type=RunEventType.RUN_FINISHED,
                    phase=RunPhase.COMPLETED,
                    stop_reason="PASS",
                    summary="Passed",
                )
            )
            second = future.result(timeout=1)
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    assert first["type"] == "snapshot"
    assert first["snapshot"]["phase"] == "running"
    assert [event["event_id"] for event in first["timeline"]] == ["evt-1"]
    assert second["type"] == "event"
    assert second["event"]["event_id"] == "evt-2"
    assert second["snapshot"]["phase"] == "completed"


def test_webui_state_concurrent_publish_preserves_all_events() -> None:
    state = WebUIState(mode="live", run_id="run-1")

    def publish(index: int) -> None:
        state.publish(
            RunEvent(
                event_id=f"evt-{index}",
                run_id="run-1",
                event_type=RunEventType.ROUND_STARTED,
                round_index=index,
                phase=RunPhase.RUNNING,
                summary=f"Round {index}",
            )
        )

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(publish, range(20)))

    timeline = state.snapshot()["timeline"]

    assert len(timeline) == 20
    assert {event["event_id"] for event in timeline} == {f"evt-{index}" for index in range(20)}


def test_snapshot_display_values_do_not_use_raw_unknown_none_or_null() -> None:
    state = WebUIState(mode="demo", run_id="run-1")

    display = state.display_snapshot()
    rendered = " ".join(str(value).lower() for value in display.values())

    assert "unknown" not in rendered
    assert "none" not in rendered
    assert "null" not in rendered
    assert display["stop_reason"] == "Not available"

