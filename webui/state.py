from __future__ import annotations

import asyncio
import threading
from dataclasses import dataclass
from typing import Any

from harness.approval import ApprovalBroker
from harness.governance.hitl import HITLState
from harness.models import Action, HITLRequest
from harness.run_events import RunEvent, apply_event_to_snapshot, sanitize_event_metadata


@dataclass(frozen=True)
class Subscription:
    loop: asyncio.AbstractEventLoop
    queue: asyncio.Queue[dict[str, Any]]


class WebUIState:
    def __init__(self, *, mode: str = "demo", run_id: str = "demo") -> None:
        self.mode = mode
        self.run_id = run_id
        self.hitl_state = HITLState()
        self.approval_broker = ApprovalBroker(
            self.hitl_state,
            on_change=self._broadcast_snapshot,
        )
        self._lock = threading.RLock()
        self._snapshot = apply_event_to_snapshot(None, None)
        self._timeline: list[dict[str, Any]] = []
        self._subscriptions: list[Subscription] = []

    def publish(self, event: RunEvent) -> None:
        event_payload = event.to_dict()
        with self._lock:
            self._snapshot = apply_event_to_snapshot(self._snapshot, event)
            self._timeline.append(event_payload)
            message = {
                "type": "event",
                "event": event_payload,
                "snapshot": self._snapshot_payload_locked(),
                "timeline": list(self._timeline),
            }
            subscriptions = list(self._subscriptions)
        for subscription in subscriptions:
            subscription.loop.call_soon_threadsafe(subscription.queue.put_nowait, message)

    def update_status(
        self,
        *,
        phase: str | None = None,
        round_number: int | None = None,
        test_status: str | None = None,
        test_summary: dict[str, int] | None = None,
        failure_type: str | None | object = None,
        failure_details: list[dict[str, Any]] | None = None,
        strategy: str | None = None,
        stop_reason: str | None = None,
        clear_failure_type: bool = False,
        clear_failure_details: bool = False,
        clear_stop_reason: bool = False,
    ) -> None:
        with self._lock:
            if phase is not None:
                self._snapshot["phase"] = phase
                self._snapshot["status"] = _status_for_legacy_phase(phase)
            if round_number is not None:
                self._snapshot["round_index"] = round_number
            if test_status is not None:
                self._snapshot["test_status"] = test_status
            if test_summary is not None:
                self._snapshot["test_summary"] = {
                    "passed": int(test_summary.get("passed", 0)),
                    "failed": int(test_summary.get("failed", 0)),
                }
            if failure_type is not None:
                self._snapshot["failure_type"] = failure_type
            elif clear_failure_type:
                self._snapshot["failure_type"] = None
            if failure_details is not None:
                self._snapshot["failure_details"] = sanitize_event_metadata(
                    {"failure_details": failure_details}
                )["failure_details"]
            elif clear_failure_details:
                self._snapshot["failure_details"] = []
            if strategy is not None:
                self._snapshot["strategy"] = strategy
            if stop_reason is not None:
                self._snapshot["stop_reason"] = stop_reason
            elif clear_stop_reason:
                self._snapshot["stop_reason"] = None
            message = self._snapshot_message_locked()
            subscriptions = list(self._subscriptions)
        for subscription in subscriptions:
            subscription.loop.call_soon_threadsafe(subscription.queue.put_nowait, message)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            payload = self._snapshot_payload_locked()
            payload["timeline"] = list(self._timeline)
            return payload

    def display_snapshot(self) -> dict[str, str]:
        snapshot = self.snapshot()
        return {
            "phase": _display_value(snapshot.get("phase")),
            "status": _display_value(snapshot.get("status")),
            "round": str(snapshot.get("round_index", 0)),
            "tests": _display_value(snapshot.get("test_status")),
            "stop_reason": _display_value(snapshot.get("stop_reason")),
        }

    def subscribe(self) -> Subscription:
        subscription = Subscription(
            loop=asyncio.get_running_loop(),
            queue=asyncio.Queue(),
        )
        with self._lock:
            self._subscriptions.append(subscription)
            subscription.queue.put_nowait(self._snapshot_message_locked())
        return subscription

    def unsubscribe(self, subscription: Subscription) -> None:
        with self._lock:
            if subscription in self._subscriptions:
                self._subscriptions.remove(subscription)

    def create_hitl_request(self, action: Action, timeout: int) -> HITLRequest:
        return self.approval_broker.create_pending(action, timeout)

    def request_approval(self, action: Action, timeout: int) -> HITLRequest:
        return self.approval_broker.request(action, timeout)

    def decide_hitl(self, request_id: str, decision: str) -> HITLRequest:
        return self.approval_broker.resolve(request_id, decision)

    def _broadcast_snapshot(self) -> None:
        with self._lock:
            message = self._snapshot_message_locked()
            subscriptions = list(self._subscriptions)
        for subscription in subscriptions:
            subscription.loop.call_soon_threadsafe(subscription.queue.put_nowait, message)

    def _snapshot_message_locked(self) -> dict[str, Any]:
        return {
            "type": "snapshot",
            "snapshot": self._snapshot_payload_locked(),
            "timeline": list(self._timeline),
        }

    def _snapshot_payload_locked(self) -> dict[str, Any]:
        summary = self._snapshot.get("test_summary")
        if not isinstance(summary, dict):
            summary = {"passed": 0, "failed": 0}
        return {
            "mode": self.mode,
            "run_id": self.run_id,
            "phase": self._snapshot.get("phase"),
            "status": self._snapshot.get("status"),
            "round_index": self._snapshot.get("round_index", 0),
            "round_number": self._snapshot.get("round_index", 0),
            "test_status": self._snapshot.get("test_status"),
            "test_summary": {
                "passed": int(summary.get("passed", 0)),
                "failed": int(summary.get("failed", 0)),
            },
            "failure_type": self._snapshot.get("failure_type"),
            "failure_details": list(self._snapshot.get("failure_details", [])),
            "strategy": self._snapshot.get("strategy", ""),
            "stop_reason": self._snapshot.get("stop_reason"),
            "pending_hitl": [
                _serialize_hitl_request(request)
                for request in self.hitl_state.get_pending()
            ],
        }


def _serialize_hitl_request(request: HITLRequest) -> dict[str, Any]:
    return {
        "request_id": request.request_id,
        "status": request.status.value,
        "decision": request.decision,
        "action": {
            "tool_name": request.action.tool_name,
            "args": sanitize_event_metadata({"args": request.action.args})["args"],
        },
    }


def _display_value(value: object) -> str:
    if value is None or value == "":
        return "Not available"
    rendered = str(value)
    if rendered.lower() in {"unknown", "none", "null", "undefined"}:
        return "Not available"
    return rendered


def _status_for_legacy_phase(phase: str) -> str:
    return {
        "idle": "Not started",
        "red": "Running tests",
        "green": "Completed",
        "running": "Running",
        "testing": "Running tests",
        "awaiting_approval": "Awaiting approval",
        "completed": "Completed",
        "failed": "Failed",
    }.get(phase, "Running")
