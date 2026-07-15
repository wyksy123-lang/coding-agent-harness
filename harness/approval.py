from __future__ import annotations

import threading
from collections.abc import Callable

from harness.governance.hitl import HITLState
from harness.models import Action, HITLRequest, HITLStatus


class ApprovalBroker:
    """Thread-safe bridge between AgentLoop HITL requests and UI decisions."""

    def __init__(
        self,
        hitl_state: HITLState | None = None,
        *,
        on_change: Callable[[], None] | None = None,
    ) -> None:
        self._hitl_state = hitl_state or HITLState()
        self._condition = threading.Condition()
        self._on_change = on_change

    @property
    def hitl_state(self) -> HITLState:
        return self._hitl_state

    def request(self, action: Action, timeout: int) -> HITLRequest:
        request = self.create_pending(action, timeout)
        with self._condition:
            resolved = self._condition.wait_for(
                lambda: request.status != HITLStatus.PENDING,
                timeout=timeout,
            )
            if not resolved and request.status == HITLStatus.PENDING:
                request.status = HITLStatus.TIMEOUT
                request.decision = "timeout"
                self._condition.notify_all()
        if not resolved:
            self._notify_change()
        return request

    def create_pending(self, action: Action, timeout: int) -> HITLRequest:
        with self._condition:
            request = self._hitl_state.create(action, timeout)
            self._condition.notify_all()
        self._notify_change()
        return request

    def resolve(self, request_id: str, decision: str) -> HITLRequest:
        normalized = decision.lower()
        with self._condition:
            if normalized in {"approve", "approved"}:
                request = self._hitl_state.approve(request_id)
            elif normalized in {"deny", "denied"}:
                request = self._hitl_state.deny(request_id)
            else:
                raise ValueError("decision must be approve or deny")
            self._condition.notify_all()
        self._notify_change()
        return request

    def cancel_all(self) -> list[HITLRequest]:
        with self._condition:
            cancelled = list(self._hitl_state.get_pending())
            for request in cancelled:
                request.status = HITLStatus.TIMEOUT
                request.decision = "cancelled"
            self._condition.notify_all()
        if cancelled:
            self._notify_change()
        return cancelled

    def pending(self) -> list[HITLRequest]:
        with self._condition:
            return list(self._hitl_state.get_pending())

    def wait_for_pending(self, *, timeout: float) -> HITLRequest:
        with self._condition:
            found = self._condition.wait_for(
                lambda: bool(self._hitl_state.get_pending()),
                timeout=timeout,
            )
            if not found:
                raise TimeoutError("no pending HITL request appeared")
            return self._hitl_state.get_pending()[0]

    def _notify_change(self) -> None:
        if self._on_change is not None:
            self._on_change()
