from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from harness.approval import ApprovalBroker
from harness.models import Action, HITLStatus


def _action() -> Action:
    return Action(tool_name="run_command", args={"cmd": "rm -rf build"})


def test_approval_broker_request_waits_until_approved() -> None:
    broker = ApprovalBroker()

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(broker.request, _action(), 30)
        request = broker.wait_for_pending(timeout=1)

        resolved = broker.resolve(request.request_id, "approve")
        completed = future.result(timeout=1)

    assert resolved.status == HITLStatus.APPROVED
    assert completed.status == HITLStatus.APPROVED
    assert completed.decision == "approved"
    assert broker.pending() == []


def test_approval_broker_denial_resolves_request_for_agent_feedback() -> None:
    broker = ApprovalBroker()

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(broker.request, _action(), 30)
        request = broker.wait_for_pending(timeout=1)

        broker.resolve(request.request_id, "deny")
        completed = future.result(timeout=1)

    assert completed.status == HITLStatus.DENIED
    assert completed.decision == "denied"


def test_approval_broker_rejects_duplicate_decision() -> None:
    broker = ApprovalBroker()
    request = broker.create_pending(_action(), timeout=30)

    broker.resolve(request.request_id, "approve")

    with pytest.raises(ValueError):
        broker.resolve(request.request_id, "deny")


def test_approval_broker_rejects_unknown_request_id() -> None:
    broker = ApprovalBroker()

    with pytest.raises(KeyError):
        broker.resolve("missing", "approve")


def test_approval_broker_cancel_all_resolves_pending_requests() -> None:
    broker = ApprovalBroker()
    first = broker.create_pending(_action(), timeout=30)
    second = broker.create_pending(_action(), timeout=30)

    cancelled = broker.cancel_all()

    assert [request.request_id for request in cancelled] == [
        first.request_id,
        second.request_id,
    ]
    assert {request.status for request in cancelled} == {HITLStatus.TIMEOUT}
    assert broker.pending() == []

