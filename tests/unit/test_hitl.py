from __future__ import annotations

from datetime import datetime

import pytest

from harness.governance.hitl import HITLState
from harness.models import Action, HITLRequest, HITLStatus


def _make_action(tool_name: str = "run_command", cmd: str = "ls -la") -> Action:
    """Build a minimal ``Action`` for use in HITL tests."""
    return Action(tool_name=tool_name, args={"cmd": cmd})


# ---------------------------------------------------------------------------
# Design decisions (provisional — the Green subagent must align):
#
# 1. ``request_id``: The existing ``HITLRequest`` dataclass in
#    ``harness/models.py`` has no ``request_id`` field.  These tests assume
#    the implementation adds a ``request_id: str`` attribute to
#    ``HITLRequest`` (or otherwise exposes it) so that the value returned by
#    ``create()`` can be fed back into ``approve``/``deny``/``check_timeout``.
#
# 2. Exception types: Illegal state transitions are expected to raise
#    ``ValueError``.  Operations on an unknown ``request_id`` are expected
#    to raise ``KeyError``.  If the implementation chooses different
#    exception types the Green subagent must update these assertions.
#
# 3. ``decision`` field: The spec does not pin down the exact string value
#    after a transition.  Tests only assert that ``decision`` is a non-empty
#    string once a decision has been recorded (the authoritative signal is
#    ``status``).
#
# 4. Instance-based state: ``HITLState`` is expected to be instantiated
#    (``HITLState()``) with per-instance state so that multiple instances
#    are independent.  Methods may be static or instance methods — calling
#    them on an instance works either way.
# ---------------------------------------------------------------------------


class TestHITLStateExistence:
    """Verify ``HITLState`` is importable and has the expected API surface."""

    def test_hitl_state_is_class(self):
        assert isinstance(HITLState, type)

    def test_hitl_state_has_create_method(self):
        assert hasattr(HITLState, "create")

    def test_hitl_state_has_approve_method(self):
        assert hasattr(HITLState, "approve")

    def test_hitl_state_has_deny_method(self):
        assert hasattr(HITLState, "deny")

    def test_hitl_state_has_check_timeout_method(self):
        assert hasattr(HITLState, "check_timeout")

    def test_hitl_state_has_get_pending_method(self):
        assert hasattr(HITLState, "get_pending")

    def test_create_is_callable(self):
        assert callable(getattr(HITLState, "create", None))

    def test_approve_is_callable(self):
        assert callable(getattr(HITLState, "approve", None))

    def test_deny_is_callable(self):
        assert callable(getattr(HITLState, "deny", None))

    def test_check_timeout_is_callable(self):
        assert callable(getattr(HITLState, "check_timeout", None))

    def test_get_pending_is_callable(self):
        assert callable(getattr(HITLState, "get_pending", None))


class TestHITLStateCreate:
    """``create()`` must produce a PENDING ``HITLRequest``."""

    def test_create_returns_hitl_request(self):
        request = HITLState().create(_make_action(), timeout=300)
        assert isinstance(request, HITLRequest)

    def test_create_status_is_pending(self):
        request = HITLState().create(_make_action(), timeout=300)
        assert request.status == HITLStatus.PENDING

    def test_create_timestamp_is_datetime(self):
        request = HITLState().create(_make_action(), timeout=300)
        assert isinstance(request.timestamp, datetime)

    def test_create_timestamp_close_to_now(self):
        now = datetime.now()
        request = HITLState().create(_make_action(), timeout=300)
        delta = abs((request.timestamp - now).total_seconds())
        assert delta < 5

    def test_create_action_stored_correctly(self):
        action = _make_action(tool_name="run_command", cmd="rm -rf /tmp")
        request = HITLState().create(action, timeout=300)
        assert request.action is action

    def test_create_action_tool_name_preserved(self):
        action = _make_action(tool_name="write_file", cmd="x")
        request = HITLState().create(action, timeout=300)
        assert request.action.tool_name == "write_file"

    def test_create_action_args_preserved(self):
        action = _make_action(tool_name="run_command", cmd="git push")
        request = HITLState().create(action, timeout=300)
        assert request.action.args == {"cmd": "git push"}

    def test_create_decision_is_empty_string(self):
        request = HITLState().create(_make_action(), timeout=300)
        assert request.decision == ""

    def test_create_assigns_request_id(self):
        request = HITLState().create(_make_action(), timeout=300)
        assert hasattr(request, "request_id")

    def test_create_request_id_is_string(self):
        request = HITLState().create(_make_action(), timeout=300)
        assert isinstance(request.request_id, str)

    def test_create_request_id_is_non_empty(self):
        request = HITLState().create(_make_action(), timeout=300)
        assert request.request_id != ""

    def test_create_request_id_is_unique(self):
        state = HITLState()
        r1 = state.create(_make_action(cmd="ls"), timeout=300)
        r2 = state.create(_make_action(cmd="ls"), timeout=300)
        assert r1.request_id != r2.request_id

    def test_create_appears_in_get_pending(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=300)
        pending = state.get_pending()
        assert request in pending

    def test_create_timeout_stored_for_check_timeout(self):
        """A request created with ``timeout=0`` must immediately time out."""
        state = HITLState()
        request = state.create(_make_action(), timeout=0)
        result = state.check_timeout(request.request_id)
        assert result.status == HITLStatus.TIMEOUT


class TestHITLStateApprove:
    """``approve()`` must transition PENDING → APPROVED."""

    def test_approve_transitions_to_approved(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=300)
        result = state.approve(request.request_id)
        assert result.status == HITLStatus.APPROVED

    def test_approve_returns_hitl_request(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=300)
        result = state.approve(request.request_id)
        assert isinstance(result, HITLRequest)

    def test_approve_updates_decision(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=300)
        result = state.approve(request.request_id)
        assert result.decision != ""

    def test_approve_preserves_action(self):
        state = HITLState()
        action = _make_action(tool_name="run_command", cmd="rm -rf /")
        request = state.create(action, timeout=300)
        result = state.approve(request.request_id)
        assert result.action is action

    def test_approved_not_in_get_pending(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=300)
        state.approve(request.request_id)
        pending = state.get_pending()
        assert request not in pending
        assert all(r.status == HITLStatus.PENDING for r in pending)

    def test_approve_returns_same_request_id(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=300)
        result = state.approve(request.request_id)
        assert result.request_id == request.request_id


class TestHITLStateDeny:
    """``deny()`` must transition PENDING → DENIED."""

    def test_deny_transitions_to_denied(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=300)
        result = state.deny(request.request_id)
        assert result.status == HITLStatus.DENIED

    def test_deny_returns_hitl_request(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=300)
        result = state.deny(request.request_id)
        assert isinstance(result, HITLRequest)

    def test_deny_updates_decision(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=300)
        result = state.deny(request.request_id)
        assert result.decision != ""

    def test_deny_preserves_action(self):
        state = HITLState()
        action = _make_action(tool_name="run_command", cmd="git push")
        request = state.create(action, timeout=300)
        result = state.deny(request.request_id)
        assert result.action is action

    def test_denied_not_in_get_pending(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=300)
        state.deny(request.request_id)
        pending = state.get_pending()
        assert request not in pending
        assert all(r.status == HITLStatus.PENDING for r in pending)

    def test_deny_returns_same_request_id(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=300)
        result = state.deny(request.request_id)
        assert result.request_id == request.request_id


class TestHITLStateCheckTimeout:
    """``check_timeout()`` must transition PENDING → TIMEOUT when elapsed."""

    def test_check_timeout_elapsed_transitions_to_timeout(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=0)
        result = state.check_timeout(request.request_id)
        assert result.status == HITLStatus.TIMEOUT

    def test_check_timeout_not_elapsed_stays_pending(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=3600)
        result = state.check_timeout(request.request_id)
        assert result.status == HITLStatus.PENDING

    def test_check_timeout_returns_hitl_request(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=0)
        result = state.check_timeout(request.request_id)
        assert isinstance(result, HITLRequest)

    def test_check_timeout_updates_decision(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=0)
        result = state.check_timeout(request.request_id)
        assert result.decision != ""

    def test_timeout_not_in_get_pending(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=0)
        state.check_timeout(request.request_id)
        pending = state.get_pending()
        assert request not in pending
        assert all(r.status == HITLStatus.PENDING for r in pending)

    def test_check_timeout_returns_same_request_id(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=0)
        result = state.check_timeout(request.request_id)
        assert result.request_id == request.request_id

    def test_check_timeout_preserves_action(self):
        state = HITLState()
        action = _make_action(tool_name="run_command", cmd="docker run")
        request = state.create(action, timeout=0)
        result = state.check_timeout(request.request_id)
        assert result.action is action

    def test_check_timeout_not_elapsed_no_decision_change(self):
        """When timeout has not elapsed, ``decision`` should remain unchanged."""
        state = HITLState()
        request = state.create(_make_action(), timeout=3600)
        result = state.check_timeout(request.request_id)
        assert result.decision == request.decision


class TestHITLStateGetPending:
    """``get_pending()`` must return only PENDING requests."""

    def test_get_pending_empty_initially(self):
        state = HITLState()
        assert state.get_pending() == []

    def test_get_pending_returns_list(self):
        state = HITLState()
        state.create(_make_action(), timeout=300)
        pending = state.get_pending()
        assert isinstance(pending, list)

    def test_get_pending_returns_pending_requests(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=300)
        pending = state.get_pending()
        assert len(pending) == 1
        assert pending[0].status == HITLStatus.PENDING
        assert pending[0].request_id == request.request_id

    def test_get_pending_excludes_approved(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=300)
        state.approve(request.request_id)
        assert len(state.get_pending()) == 0

    def test_get_pending_excludes_denied(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=300)
        state.deny(request.request_id)
        assert len(state.get_pending()) == 0

    def test_get_pending_excludes_timeout(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=0)
        state.check_timeout(request.request_id)
        assert len(state.get_pending()) == 0

    def test_get_pending_returns_multiple(self):
        state = HITLState()
        r1 = state.create(_make_action(cmd="ls"), timeout=300)
        r2 = state.create(_make_action(cmd="pwd"), timeout=300)
        r3 = state.create(_make_action(cmd="whoami"), timeout=300)
        pending = state.get_pending()
        assert len(pending) == 3
        ids = {r.request_id for r in pending}
        assert ids == {r1.request_id, r2.request_id, r3.request_id}

    def test_get_pending_all_have_pending_status(self):
        state = HITLState()
        state.create(_make_action(cmd="ls"), timeout=300)
        state.create(_make_action(cmd="pwd"), timeout=300)
        pending = state.get_pending()
        assert all(r.status == HITLStatus.PENDING for r in pending)

    def test_get_pending_empty_after_all_resolved(self):
        state = HITLState()
        r1 = state.create(_make_action(cmd="ls"), timeout=300)
        r2 = state.create(_make_action(cmd="pwd"), timeout=0)
        state.approve(r1.request_id)
        state.check_timeout(r2.request_id)
        assert state.get_pending() == []


class TestHITLStateIllegalTransitions:
    """Illegal state transitions must raise ``ValueError``.

    Provisional: the implementation may define a custom exception; if so the
    Green subagent must update these ``pytest.raises`` expectations.
    """

    def test_approve_already_approved_raises(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=300)
        state.approve(request.request_id)
        with pytest.raises(ValueError):
            state.approve(request.request_id)

    def test_approve_denied_raises(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=300)
        state.deny(request.request_id)
        with pytest.raises(ValueError):
            state.approve(request.request_id)

    def test_approve_timeout_raises(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=0)
        state.check_timeout(request.request_id)
        with pytest.raises(ValueError):
            state.approve(request.request_id)

    def test_deny_already_denied_raises(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=300)
        state.deny(request.request_id)
        with pytest.raises(ValueError):
            state.deny(request.request_id)

    def test_deny_approved_raises(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=300)
        state.approve(request.request_id)
        with pytest.raises(ValueError):
            state.deny(request.request_id)

    def test_deny_timeout_raises(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=0)
        state.check_timeout(request.request_id)
        with pytest.raises(ValueError):
            state.deny(request.request_id)

    def test_check_timeout_on_approved_raises(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=300)
        state.approve(request.request_id)
        with pytest.raises(ValueError):
            state.check_timeout(request.request_id)

    def test_check_timeout_on_denied_raises(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=300)
        state.deny(request.request_id)
        with pytest.raises(ValueError):
            state.check_timeout(request.request_id)

    def test_check_timeout_on_timeout_raises(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=0)
        state.check_timeout(request.request_id)
        with pytest.raises(ValueError):
            state.check_timeout(request.request_id)


class TestHITLStateUnknownId:
    """Operations on an unknown ``request_id`` must raise ``KeyError``.

    Provisional: the implementation may raise ``ValueError`` instead; if so
    the Green subagent must update these expectations.
    """

    def test_approve_unknown_id_raises_keyerror(self):
        with pytest.raises(KeyError):
            HITLState().approve("nonexistent-id")

    def test_deny_unknown_id_raises_keyerror(self):
        with pytest.raises(KeyError):
            HITLState().deny("nonexistent-id")

    def test_check_timeout_unknown_id_raises_keyerror(self):
        with pytest.raises(KeyError):
            HITLState().check_timeout("nonexistent-id")

    def test_approve_empty_string_id_raises_keyerror(self):
        with pytest.raises(KeyError):
            HITLState().approve("")

    def test_deny_empty_string_id_raises_keyerror(self):
        with pytest.raises(KeyError):
            HITLState().deny("")

    def test_check_timeout_empty_string_id_raises_keyerror(self):
        with pytest.raises(KeyError):
            HITLState().check_timeout("")


class TestHITLStateEdgeCases:
    """Additional edge cases for robustness."""

    def test_create_none_action_raises(self):
        """``create`` with ``None`` action must raise ``ValueError``."""
        with pytest.raises(ValueError, match="action"):
            HITLState().create(None, timeout=300)  # type: ignore[arg-type]

    def test_multiple_instances_are_independent(self):
        """Two ``HITLState`` instances must not share state."""
        state1 = HITLState()
        state2 = HITLState()
        r1 = state1.create(_make_action(), timeout=300)
        assert len(state1.get_pending()) == 1
        assert len(state2.get_pending()) == 0
        state1.approve(r1.request_id)
        assert len(state1.get_pending()) == 0
        assert len(state2.get_pending()) == 0

    def test_request_id_unique_across_multiple_creates(self):
        state = HITLState()
        ids = set()
        for i in range(10):
            request = state.create(_make_action(cmd=f"cmd{i}"), timeout=300)
            assert request.request_id not in ids
            ids.add(request.request_id)
        assert len(ids) == 10

    def test_request_id_unique_across_instances(self):
        state1 = HITLState()
        state2 = HITLState()
        r1 = state1.create(_make_action(), timeout=300)
        r2 = state2.create(_make_action(), timeout=300)
        assert r1.request_id != r2.request_id

    def test_create_with_zero_timeout_immediately_times_out(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=0)
        result = state.check_timeout(request.request_id)
        assert result.status == HITLStatus.TIMEOUT

    def test_create_with_large_timeout_stays_pending(self):
        state = HITLState()
        request = state.create(_make_action(), timeout=999999)
        result = state.check_timeout(request.request_id)
        assert result.status == HITLStatus.PENDING

    def test_mixed_transitions_on_different_requests(self):
        """Approve one, deny another, timeout a third — all independent."""
        state = HITLState()
        r1 = state.create(_make_action(cmd="ls"), timeout=300)
        r2 = state.create(_make_action(cmd="pwd"), timeout=300)
        r3 = state.create(_make_action(cmd="rm"), timeout=0)
        approved = state.approve(r1.request_id)
        denied = state.deny(r2.request_id)
        timed_out = state.check_timeout(r3.request_id)
        assert approved.status == HITLStatus.APPROVED
        assert denied.status == HITLStatus.DENIED
        assert timed_out.status == HITLStatus.TIMEOUT
        assert state.get_pending() == []

    def test_approve_then_get_pending_excludes_only_approved(self):
        """Approving one request leaves others pending."""
        state = HITLState()
        r1 = state.create(_make_action(cmd="ls"), timeout=300)
        r2 = state.create(_make_action(cmd="pwd"), timeout=300)
        state.approve(r1.request_id)
        pending = state.get_pending()
        assert len(pending) == 1
        assert pending[0].request_id == r2.request_id

    def test_deny_then_get_pending_excludes_only_denied(self):
        """Denying one request leaves others pending."""
        state = HITLState()
        r1 = state.create(_make_action(cmd="ls"), timeout=300)
        r2 = state.create(_make_action(cmd="pwd"), timeout=300)
        state.deny(r1.request_id)
        pending = state.get_pending()
        assert len(pending) == 1
        assert pending[0].request_id == r2.request_id

    def test_timeout_then_get_pending_excludes_only_timed_out(self):
        """Timing out one request leaves others pending."""
        state = HITLState()
        r1 = state.create(_make_action(cmd="ls"), timeout=0)
        r2 = state.create(_make_action(cmd="pwd"), timeout=300)
        state.check_timeout(r1.request_id)
        pending = state.get_pending()
        assert len(pending) == 1
        assert pending[0].request_id == r2.request_id
