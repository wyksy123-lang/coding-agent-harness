from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass, field
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from harness.governance.hitl import HITLState
from harness.models import Action, HITLRequest

_UNSET = object()
_SENSITIVE_NAME_RE = re.compile(
    r"(api[_-]?key|token|secret|password|path|cwd|dir|directory|file)",
    re.IGNORECASE,
)
_HIGH_CONFIDENCE_SECRET_RE = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY)"
)
_SENSITIVE_CONTENT_RE = re.compile(
    r"(api[_-]?key|token|secret|password)\s*[:=]\s*\S+",
    re.IGNORECASE,
)
_PATH_LIKE_RE = re.compile(
    r"([A-Za-z]:\\\S+|\\\\\S+|/\S+|\S*[\\/]\S+|[\w.-]+\.[A-Za-z0-9]{1,8})"
)


@dataclass(frozen=True)
class _Subscription:
    loop: asyncio.AbstractEventLoop
    queue: asyncio.Queue[dict[str, Any]]


def _redact_value(name: str, value: Any) -> Any:
    if _SENSITIVE_NAME_RE.search(name):
        return "[redacted]"
    if isinstance(value, str):
        return _redact_string(value)
    if isinstance(value, dict):
        return {str(key): _redact_value(str(key), item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_value(name, item) for item in value]
    return value


def _redact_string(value: str) -> str:
    redacted = _HIGH_CONFIDENCE_SECRET_RE.sub("[redacted]", value)
    redacted = _SENSITIVE_CONTENT_RE.sub(lambda match: f"{match.group(1)}=[redacted]", redacted)
    redacted = re.sub(r"\S*\.env\S*", "[redacted]", redacted)
    redacted = re.sub(r"C:\\Users\\\S+", "[redacted]", redacted)
    redacted = _PATH_LIKE_RE.sub("[redacted]", redacted)
    return redacted


def _serialize_action(action: Action) -> dict[str, Any]:
    return {
        "tool_name": action.tool_name,
        "args": {
            str(name): _redact_value(str(name), value)
            for name, value in action.args.items()
        },
    }


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
    test_summary: dict[str, int] = field(
        default_factory=lambda: {"passed": 0, "failed": 0}
    )
    failure_type: str | None = None
    failure_details: list[dict[str, Any]] = field(default_factory=list)
    strategy: str = ""
    stop_reason: str | None = None
    hitl_state: HITLState = field(default_factory=HITLState)
    _subscriptions: list[_Subscription] = field(default_factory=list, init=False)

    def update_status(
        self,
        *,
        phase: str | None = None,
        round_number: int | None = None,
        test_status: str | None = None,
        test_summary: dict[str, int] | None = None,
        failure_type: str | None | object = _UNSET,
        failure_details: list[dict[str, Any]] | None = None,
        strategy: str | None = None,
        stop_reason: str | None = None,
        clear_failure_type: bool = False,
        clear_failure_details: bool = False,
        clear_stop_reason: bool = False,
    ) -> None:
        if phase is not None:
            self.phase = phase
        if round_number is not None:
            self.round_number = round_number
        if test_status is not None:
            self.test_status = test_status
        if test_summary is not None:
            self.test_summary = {
                "passed": int(test_summary.get("passed", 0)),
                "failed": int(test_summary.get("failed", 0)),
            }
        if failure_type is not _UNSET:
            self.failure_type = failure_type if isinstance(failure_type, str) else None
        elif clear_failure_type:
            self.failure_type = None
        if failure_details is not None:
            self.failure_details = [
                _redact_value("failure_details", detail)
                for detail in failure_details
                if isinstance(detail, dict)
            ]
        elif clear_failure_details:
            self.failure_details = []
        if strategy is not None:
            self.strategy = strategy
        if stop_reason is not None:
            self.stop_reason = stop_reason
        elif clear_stop_reason:
            self.stop_reason = None
        self._broadcast_status()

    def snapshot(self) -> dict[str, Any]:
        return {
            "phase": self.phase,
            "round_number": self.round_number,
            "test_status": self.test_status,
            "test_summary": dict(self.test_summary),
            "failure_type": self.failure_type,
            "failure_details": list(self.failure_details),
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
            request = self.hitl_state.approve(request_id)
            self._broadcast_status()
            return request
        if normalized in {"deny", "denied"}:
            request = self.hitl_state.deny(request_id)
            self._broadcast_status()
            return request
        raise ValueError("decision must be approve or deny")

    def create_hitl_request(self, action: Action, timeout: int) -> HITLRequest:
        request = self.hitl_state.create(action, timeout)
        self._broadcast_status()
        return request

    def subscribe(self) -> _Subscription:
        subscription = _Subscription(
            loop=asyncio.get_running_loop(),
            queue=asyncio.Queue(),
        )
        self._subscriptions.append(subscription)
        subscription.queue.put_nowait(_status_message(self.snapshot()))
        return subscription

    def unsubscribe(self, subscription: _Subscription) -> None:
        if subscription in self._subscriptions:
            self._subscriptions.remove(subscription)

    def _broadcast_status(self) -> None:
        message = _status_message(self.snapshot())
        for subscription in list(self._subscriptions):
            subscription.loop.call_soon_threadsafe(subscription.queue.put_nowait, message)


class WebSocketStatusEndpoint:
    def __init__(self, state: WebUIState) -> None:
        self._state = state

    async def handle(self, websocket: WebSocket) -> None:
        await websocket.accept()
        subscription = self._state.subscribe()
        try:
            while True:
                queue_task = asyncio.create_task(subscription.queue.get())
                receive_task = asyncio.create_task(websocket.receive_json())
                done, pending = await asyncio.wait(
                    {queue_task, receive_task},
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()

                if queue_task in done:
                    await websocket.send_json(queue_task.result())
                if receive_task in done:
                    try:
                        client_message = receive_task.result()
                    except json.JSONDecodeError:
                        await websocket.send_json(
                            {"type": "error", "detail": "invalid json message"}
                        )
                        continue
                    if (
                        isinstance(client_message, dict)
                        and client_message.get("type") == "ping"
                    ):
                        await websocket.send_json({"type": "pong"})
                    else:
                        await websocket.send_json(_status_message(self._state.snapshot()))
        except WebSocketDisconnect:
            return
        finally:
            self._state.unsubscribe(subscription)


def _status_message(status: dict[str, Any]) -> dict[str, Any]:
    return {"type": "status", "status": status}
