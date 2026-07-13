from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from harness.governance.hitl import HITLState
from harness.models import Action, HITLRequest


def _serialize_action(action: Action) -> dict[str, Any]:
    return {"tool_name": action.tool_name, "args": dict(action.args)}


def _serialize_hitl_request(request: HITLRequest) -> dict[str, Any]:
    return {
        "request_id": request.request_id,
        "status": request.status.value,
        "decision": request.decision,
        "action": _serialize_action(request.action),
    }


@dataclass
class WebUIState:
    phase: str = "idle"
    round_number: int = 0
    test_status: str = "unknown"
    failure_type: str | None = None
    strategy: str = ""
    stop_reason: str | None = None
    hitl_state: HITLState = field(default_factory=HITLState)

    def update_status(
        self,
        *,
        phase: str | None = None,
        round_number: int | None = None,
        test_status: str | None = None,
        failure_type: str | None = None,
        strategy: str | None = None,
        stop_reason: str | None = None,
    ) -> None:
        if phase is not None:
            self.phase = phase
        if round_number is not None:
            self.round_number = round_number
        if test_status is not None:
            self.test_status = test_status
        self.failure_type = failure_type
        if strategy is not None:
            self.strategy = strategy
        if stop_reason is not None:
            self.stop_reason = stop_reason

    def snapshot(self) -> dict[str, Any]:
        return {
            "phase": self.phase,
            "round_number": self.round_number,
            "test_status": self.test_status,
            "failure_type": self.failure_type,
            "strategy": self.strategy,
            "stop_reason": self.stop_reason,
            "pending_hitl": [
                _serialize_hitl_request(request)
                for request in self.hitl_state.get_pending()
            ],
        }

    def decide_hitl(self, request_id: str, decision: str) -> HITLRequest:
        normalized = decision.lower()
        if normalized in {"approve", "approved"}:
            return self.hitl_state.approve(request_id)
        if normalized in {"deny", "denied"}:
            return self.hitl_state.deny(request_id)
        raise ValueError("decision must be approve or deny")


class WebSocketStatusEndpoint:
    def __init__(self, state: WebUIState) -> None:
        self._state = state

    async def handle(self, websocket: WebSocket) -> None:
        await websocket.accept()
        await self._send_status(websocket)
        try:
            while True:
                message = await websocket.receive_json()
                if isinstance(message, dict) and message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                else:
                    await self._send_status(websocket)
        except WebSocketDisconnect:
            return

    async def _send_status(self, websocket: WebSocket) -> None:
        await websocket.send_json({"type": "status", "status": self._state.snapshot()})
