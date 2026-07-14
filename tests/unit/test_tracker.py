from __future__ import annotations

import harness.feedback as feedback
from harness.feedback.tracker import RoundTracker
from harness.models import Failure, FailureType, RoundOutcome, RoundRecord, StopReason


def _record(
    round_number: int,
    *,
    fingerprint: str = "ASSERTION|tests/test_sample.py::test_example|assert 1 == 2",
    outcome: RoundOutcome = RoundOutcome.FAIL,
    strategy_used: str = "fix_assertion",
) -> RoundRecord:
    return RoundRecord(
        round_number=round_number,
        actions=[],
        failure_fingerprint=fingerprint,
        strategy_used=strategy_used,
        outcome=outcome,
    )


def _failure() -> Failure:
    return Failure(
        type=FailureType.ASSERTION,
        test_name="tests/test_sample.py::test_example",
        message="AssertionError: assert 1 == 2",
        file="tests/test_sample.py",
        line=12,
        expected="2",
        actual="1",
    )


def test_feedback_package_exports_tracker():
    assert feedback.RoundTracker is RoundTracker


def test_update_appends_round_history():
    tracker = RoundTracker(max_rounds=3, stuck_threshold=2)
    record = _record(1)

    tracker.update(record)

    assert tracker.history == [record]


def test_all_green_returns_pass_stop_reason():
    tracker = RoundTracker(max_rounds=3, stuck_threshold=2)

    tracker.update(_record(1, outcome=RoundOutcome.PASS, fingerprint=""))

    assert tracker.should_stop() == StopReason.PASS


def test_max_rounds_returns_max_rounds_stop_reason():
    tracker = RoundTracker(max_rounds=2, stuck_threshold=3)

    tracker.update(_record(1, fingerprint="one"))
    tracker.update(_record(2, fingerprint="two"))

    assert tracker.should_stop() == StopReason.MAX_ROUNDS


def test_same_fingerprint_consecutive_threshold_detects_loop_and_stops():
    tracker = RoundTracker(max_rounds=5, stuck_threshold=3)

    tracker.update(_record(1, fingerprint="same"))
    tracker.update(_record(2, fingerprint="same"))
    tracker.update(_record(3, fingerprint="same"))

    assert tracker.detect_loop() is True
    assert tracker.should_stop() == StopReason.STUCK


def test_different_fingerprints_do_not_trigger_stuck():
    tracker = RoundTracker(max_rounds=5, stuck_threshold=3)

    tracker.update(_record(1, fingerprint="same"))
    tracker.update(_record(2, fingerprint="different"))
    tracker.update(_record(3, fingerprint="same"))

    assert tracker.detect_loop() is False
    assert tracker.should_stop() is None


def test_empty_fingerprints_do_not_trigger_stuck():
    tracker = RoundTracker(max_rounds=5, stuck_threshold=3)

    tracker.update(_record(1, fingerprint=""))
    tracker.update(_record(2, fingerprint=""))
    tracker.update(_record(3, fingerprint=""))

    assert tracker.detect_loop() is False
    assert tracker.should_stop() is None


def test_hitl_denied_returns_hitl_denied_stop_reason():
    tracker = RoundTracker(max_rounds=5, stuck_threshold=3)

    tracker.update(
        _record(1, outcome=RoundOutcome.HITL_DENIED, fingerprint="dangerous-command")
    )

    assert tracker.should_stop() == StopReason.HITL_DENIED


def test_fail_before_max_rounds_and_not_stuck_continues():
    tracker = RoundTracker(max_rounds=5, stuck_threshold=3)

    tracker.update(_record(1, fingerprint="one"))
    tracker.update(_record(2, fingerprint="two"))

    assert tracker.should_stop() is None


def test_failure_fingerprint_is_deterministic_and_keeps_readable_message():
    failure = _failure()

    first = RoundTracker.failure_fingerprint(failure)
    second = RoundTracker.failure_fingerprint(failure)

    assert first == second
    assert first.startswith("ASSERTION|tests/test_sample.py::test_example|")
    stored_message = first.split("|", 2)[2]
    assert stored_message.startswith("AssertionError: assert 1 == 2")
    assert "[sha256:" in stored_message
    assert stored_message.endswith("]")
    assert len(stored_message.rsplit("[sha256:", 1)[1].rstrip("]")) == 64


def test_failure_fingerprint_truncates_long_message_but_keeps_hash():
    failure = _failure()
    failure.message = "AssertionError: " + ("very long failure detail " * 50)

    fingerprint = RoundTracker.failure_fingerprint(failure)
    stored_message = fingerprint.split("|", 2)[2]

    assert stored_message.startswith("AssertionError:")
    assert "very long failure detail very long failure detail" in stored_message
    assert len(stored_message) <= 320
    assert "[sha256:" in stored_message
