from __future__ import annotations

import pytest

import harness.feedback as feedback

from harness.feedback.injector import FeedbackInjector
from harness.models import Failure, FailureType, MemoryEntry, TestResult


EXPECTED_STRATEGY_HINTS = {
    FailureType.ASSERTION: (
        "Inspect the failing assertion, compare expected and actual values, "
        "then update the smallest code path or test fixture."
    ),
    FailureType.SYNTAX: (
        "Fix the syntax error before changing behavior; run the targeted test "
        "again after the file imports."
    ),
    FailureType.IMPORT: (
        "Resolve missing imports or module paths before debugging runtime behavior."
    ),
    FailureType.RUNTIME: (
        "Trace the exception to the smallest failing code path and add a focused "
        "guard or conversion."
    ),
    FailureType.TIMEOUT: (
        "Identify the slow or blocking operation and replace unbounded waits with "
        "bounded condition-based behavior."
    ),
    FailureType.COLLECTION: (
        "Fix pytest collection first: module names, test discovery, and import-time "
        "errors."
    ),
}


def test_feedback_package_exports_injector():
    assert feedback.FeedbackInjector is FeedbackInjector


class RecordingMemory:
    def __init__(self, entries: list[MemoryEntry]) -> None:
        self.entries = entries
        self.calls: list[tuple[FailureType, int]] = []

    def retrieve_relevant(
        self, failure_type: FailureType, limit: int = 3
    ) -> list[MemoryEntry]:
        self.calls.append((failure_type, limit))
        return self.entries


class FailingMemory:
    def retrieve_relevant(
        self, failure_type: FailureType, limit: int = 3
    ) -> list[MemoryEntry]:
        raise OSError("memory unavailable")


def _failure(
    failure_type: FailureType = FailureType.ASSERTION,
    *,
    message: str = "AssertionError: assert 1 == 2",
) -> Failure:
    return Failure(
        type=failure_type,
        test_name="tests/test_sample.py::test_example",
        message=message,
        file="tests/test_sample.py",
        line=12,
        expected="2",
        actual="1",
    )


def _test_result(failure: Failure) -> TestResult:
    return TestResult(
        status="FAIL",
        failures=[failure],
        summary={"failed": 1, "passed": 3},
    )


def _memory_entry() -> MemoryEntry:
    return MemoryEntry(
        session_id="previous-session",
        round=2,
        failure_type=FailureType.ASSERTION,
        test_name="tests/test_sample.py::test_example",
        message="AssertionError: assert 1 == 2",
        strategy_used="tighten assertion handling",
        outcome="resolved",
    )


@pytest.mark.parametrize(
    ("failure_type", "expected_hint"),
    EXPECTED_STRATEGY_HINTS.items(),
)
def test_each_failure_type_returns_deterministic_strategy_hint(
    failure_type: FailureType,
    expected_hint: str,
):
    memory = RecordingMemory([])

    feedback = FeedbackInjector.inject(
        _test_result(_failure(failure_type)),
        failure_type,
        memory,
    )

    assert feedback.failure_type == failure_type
    assert feedback.strategy_hint == expected_hint


def test_details_include_failure_location_expected_and_actual_values():
    feedback = FeedbackInjector.inject(
        _test_result(_failure()),
        FailureType.ASSERTION,
        RecordingMemory([]),
    )

    assert "tests/test_sample.py::test_example" in feedback.details
    assert "tests/test_sample.py:12" in feedback.details
    assert "expected: 2" in feedback.details
    assert "actual: 1" in feedback.details
    assert "AssertionError: assert 1 == 2" in feedback.details


def test_relevant_memory_is_retrieved_by_failure_type():
    entry = _memory_entry()
    memory = RecordingMemory([entry])

    feedback = FeedbackInjector.inject(
        _test_result(_failure()),
        FailureType.ASSERTION,
        memory,
    )

    assert feedback.relevant_memory == [entry]
    assert memory.calls == [(FailureType.ASSERTION, 3)]


def test_memory_retrieval_failure_returns_empty_memory_without_breaking_feedback():
    feedback = FeedbackInjector.inject(
        _test_result(_failure()),
        FailureType.ASSERTION,
        FailingMemory(),
    )

    assert feedback.failure_type == FailureType.ASSERTION
    assert feedback.relevant_memory == []


def test_long_feedback_details_are_bounded():
    long_message = "AssertionError: " + ("very long traceback " * 200)

    feedback = FeedbackInjector.inject(
        _test_result(_failure(message=long_message)),
        FailureType.ASSERTION,
        RecordingMemory([]),
    )

    assert len(feedback.details) <= 1200
    assert feedback.details.endswith("...")


def test_bounded_details_preserve_required_fields_when_expected_is_long():
    failure = _failure()
    failure.expected = "expected value " * 200
    failure.actual = "actual value"

    feedback = FeedbackInjector.inject(
        _test_result(failure),
        FailureType.ASSERTION,
        RecordingMemory([]),
    )

    assert len(feedback.details) <= 1200
    assert "test: tests/test_sample.py::test_example" in feedback.details
    assert "location: tests/test_sample.py:12" in feedback.details
    assert "expected: expected value" in feedback.details
    assert "actual: actual value" in feedback.details
    assert "message: AssertionError: assert 1 == 2" in feedback.details
