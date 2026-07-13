from __future__ import annotations

from fastapi.testclient import TestClient

from harness.models import Action
from webui.app import WebUIState, create_app


def test_get_root_returns_html_page() -> None:
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Coding Agent Harness" in response.text


def test_get_status_returns_current_agent_status() -> None:
    state = WebUIState()
    state.update_status(
        phase="green",
        round_number=2,
        test_status="PASS",
        failure_type=None,
        strategy="tests_passed",
        stop_reason="PASS",
    )
    client = TestClient(create_app(state))

    response = client.get("/api/status")

    assert response.status_code == 200
    assert response.json() == {
        "phase": "green",
        "round_number": 2,
        "test_status": "PASS",
        "failure_type": None,
        "strategy": "tests_passed",
        "stop_reason": "PASS",
        "pending_hitl": [],
    }


def test_websocket_sends_current_status_on_connect() -> None:
    state = WebUIState()
    state.update_status(phase="red", round_number=1, test_status="FAIL")
    client = TestClient(create_app(state))

    with client.websocket_connect("/ws") as websocket:
        message = websocket.receive_json()

    assert message["type"] == "status"
    assert message["status"]["phase"] == "red"
    assert message["status"]["round_number"] == 1
    assert message["status"]["test_status"] == "FAIL"


def test_hitl_approval_endpoint_updates_pending_request() -> None:
    state = WebUIState()
    request = state.hitl_state.create(
        Action(tool_name="run_command", args={"cmd": "rm -rf workspace"}),
        timeout=30,
    )
    client = TestClient(create_app(state))

    response = client.post(
        f"/api/hitl/{request.request_id}",
        json={"decision": "approve"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "request_id": request.request_id,
        "status": "APPROVED",
        "decision": "approved",
    }
    assert state.hitl_state.get_pending() == []


def test_hitl_approval_endpoint_rejects_invalid_decision() -> None:
    state = WebUIState()
    request = state.hitl_state.create(
        Action(tool_name="run_command", args={"cmd": "rm -rf workspace"}),
        timeout=30,
    )
    client = TestClient(create_app(state))

    response = client.post(
        f"/api/hitl/{request.request_id}",
        json={"decision": "maybe"},
    )

    assert response.status_code == 400
    assert "decision" in response.json()["detail"]
