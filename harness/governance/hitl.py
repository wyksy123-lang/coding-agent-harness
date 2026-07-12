from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from harness.models import Action, HITLRequest, HITLStatus


class HITLState:
    """Human-in-the-loop approval state machine (SPEC §3.4.3).

    Manages the lifecycle of an ``Action`` awaiting human approval:

    .. code-block:: text

        PENDING --user approve--> APPROVED --execute command--> RESUME
        PENDING --user deny-----> DENIED --feedback to agent--> RESUME
        PENDING --timeout-------> TIMEOUT --feedback to agent--> RESUME

    Each instance maintains independent state.  Timeout is controlled by
    the ``hitl_timeout_seconds`` configuration; on timeout the request
    defaults to ``DENIED`` semantics (status ``TIMEOUT``).
    """

    def __init__(self) -> None:
        self._requests: dict[str, HITLRequest] = {}
        self._timeouts: dict[str, int] = {}

    def create(self, action: Action | None, timeout: int) -> HITLRequest:
        """Create a PENDING ``HITLRequest`` for *action*.

        Raises ``ValueError`` if *action* is ``None``.
        """
        if action is None:
            raise ValueError("action must not be None")
        request_id = str(uuid4())
        request = HITLRequest(
            action=action,
            status=HITLStatus.PENDING,
            timestamp=datetime.now(),
            decision="",
            request_id=request_id,
        )
        self._requests[request_id] = request
        self._timeouts[request_id] = timeout
        return request

    def approve(self, request_id: str) -> HITLRequest:
        """Transition the request PENDING → APPROVED.

        Raises ``KeyError`` if *request_id* is unknown.
        Raises ``ValueError`` if the request is not PENDING.
        """
        if request_id not in self._requests:
            raise KeyError(request_id)
        request = self._requests[request_id]
        if request.status != HITLStatus.PENDING:
            raise ValueError(
                f"cannot approve request in status {request.status.name}"
            )
        request.status = HITLStatus.APPROVED
        request.decision = "approved"
        return request

    def deny(self, request_id: str) -> HITLRequest:
        """Transition the request PENDING → DENIED.

        Raises ``KeyError`` if *request_id* is unknown.
        Raises ``ValueError`` if the request is not PENDING.
        """
        if request_id not in self._requests:
            raise KeyError(request_id)
        request = self._requests[request_id]
        if request.status != HITLStatus.PENDING:
            raise ValueError(
                f"cannot deny request in status {request.status.name}"
            )
        request.status = HITLStatus.DENIED
        request.decision = "denied"
        return request

    def check_timeout(self, request_id: str) -> HITLRequest:
        """Transition the request PENDING → TIMEOUT if the timeout elapsed.

        If the timeout has not elapsed the request remains PENDING and is
        returned unchanged.  Raises ``KeyError`` if *request_id* is unknown.
        Raises ``ValueError`` if the request is not PENDING.
        """
        if request_id not in self._requests:
            raise KeyError(request_id)
        request = self._requests[request_id]
        if request.status != HITLStatus.PENDING:
            raise ValueError(
                f"cannot check timeout for request in status "
                f"{request.status.name}"
            )
        timeout = self._timeouts[request_id]
        elapsed = (datetime.now() - request.timestamp).total_seconds()
        if elapsed >= timeout:
            request.status = HITLStatus.TIMEOUT
            request.decision = "timeout"
        return request

    def get_pending(self) -> list[HITLRequest]:
        """Return all requests currently in the PENDING status."""
        return [
            request
            for request in self._requests.values()
            if request.status == HITLStatus.PENDING
        ]
