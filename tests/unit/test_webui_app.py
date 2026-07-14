from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any

from fastapi.testclient import TestClient

from harness.models import Action
from webui.app import WebUIState, create_app


def test_get_root_returns_html_page() -> None:
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Coding Agent Harness" in response.text
    assert 'href="/static/style.css"' in response.text
    assert 'src="/static/app.js"' in response.text
    for element_id in [
        "phase-value",
        "test-status-value",
        "failure-type-value",
        "round-number-value",
        "stop-reason-value",
        "hitl-list",
    ]:
        assert f'id="{element_id}"' in response.text


def test_static_frontend_assets_are_served() -> None:
    client = TestClient(create_app())

    app_js = client.get("/static/app.js")
    style_css = client.get("/static/style.css")

    assert app_js.status_code == 200
    assert "new WebSocket" in app_js.text
    assert "approve" in app_js.text
    assert "deny" in app_js.text
    assert style_css.status_code == 200
    assert "#hitl-list" in style_css.text


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


def test_websocket_pushes_status_updates_after_connect() -> None:
    state = WebUIState()
    client = TestClient(create_app(state))
    executor = ThreadPoolExecutor(max_workers=1)

    try:
        with client.websocket_connect("/ws") as websocket:
            websocket.receive_json()
            future = executor.submit(websocket.receive_json)
            state.update_status(phase="green", round_number=2, test_status="PASS")
            message = future.result(timeout=1)
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    assert message["type"] == "status"
    assert message["status"]["phase"] == "green"
    assert message["status"]["round_number"] == 2
    assert message["status"]["test_status"] == "PASS"


def test_websocket_replies_to_ping() -> None:
    client = TestClient(create_app())

    with client.websocket_connect("/ws") as websocket:
        websocket.receive_json()
        websocket.send_json({"type": "ping"})
        message = websocket.receive_json()

    assert message == {"type": "pong"}


def test_websocket_malformed_message_returns_error() -> None:
    client = TestClient(create_app())

    with client.websocket_connect("/ws") as websocket:
        websocket.receive_json()
        websocket.send_text("not-json")
        message = websocket.receive_json()

    assert message["type"] == "error"
    assert "json" in message["detail"].lower()


def test_status_redacts_sensitive_hitl_action_args() -> None:
    state = WebUIState()
    state.hitl_state.create(
        Action(
            tool_name="run_command",
            args={
                "cmd": "cat C:\\Users\\example\\.env",
                "api_key": "fake-secret-value",
            },
        ),
        timeout=30,
    )
    client = TestClient(create_app(state))

    response = client.get("/api/status")

    pending = response.json()["pending_hitl"]
    assert pending[0]["action"]["args"]["cmd"] == "[redacted]"
    assert pending[0]["action"]["args"]["api_key"] == "[redacted]"


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


def test_hitl_approval_endpoint_returns_not_found_for_unknown_request() -> None:
    client = TestClient(create_app(WebUIState()))

    response = client.post("/api/hitl/missing", json={"decision": "approve"})

    assert response.status_code == 404


def test_hitl_approval_endpoint_denies_pending_request() -> None:
    state = WebUIState()
    request = state.hitl_state.create(
        Action(tool_name="run_command", args={"cmd": "rm -rf workspace"}),
        timeout=30,
    )
    client = TestClient(create_app(state))

    response = client.post(
        f"/api/hitl/{request.request_id}",
        json={"decision": "deny"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "DENIED"
    assert response.json()["decision"] == "denied"


def test_update_status_preserves_failure_type_when_omitted() -> None:
    state = WebUIState()
    state.update_status(phase="red", failure_type="ASSERTION")

    state.update_status(round_number=2)

    assert state.snapshot()["failure_type"] == "ASSERTION"


def test_update_status_can_clear_failure_type() -> None:
    state = WebUIState()
    state.update_status(phase="red", failure_type="ASSERTION")

    state.update_status(failure_type=None, clear_failure_type=True)

    assert state.snapshot()["failure_type"] is None


def test_websocket_pushes_hitl_pending_updates_after_connect() -> None:
    state = WebUIState()
    client = TestClient(create_app(state))
    executor = ThreadPoolExecutor(max_workers=1)
    action_args: dict[str, Any] = {"cmd": "rm -rf workspace"}

    try:
        with client.websocket_connect("/ws") as websocket:
            websocket.receive_json()
            future = executor.submit(websocket.receive_json)
            state.create_hitl_request(
                Action(tool_name="run_command", args=action_args),
                timeout=30,
            )
            message = future.result(timeout=1)
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    assert message["type"] == "status"
    assert len(message["status"]["pending_hitl"]) == 1


def test_hitl_approval_endpoint_rejects_invalid_json_body() -> None:
    state = WebUIState()
    request = state.hitl_state.create(
        Action(tool_name="run_command", args={"cmd": "rm -rf workspace"}),
        timeout=30,
    )
    client = TestClient(create_app(state))

    response = client.post(
        f"/api/hitl/{request.request_id}",
        content="{not-json",
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 400
    assert "json" in response.json()["detail"].lower()
