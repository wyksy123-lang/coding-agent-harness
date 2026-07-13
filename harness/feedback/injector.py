from __future__ import annotations

from collections.abc import Mapping
from typing import ClassVar

from harness.memory.retriever import MemoryRetriever
from harness.models import FeedbackMessage, Failure, FailureType, MemoryEntry, TestResult


class FeedbackInjector:
    """Build structured feedback from test failures and relevant memory."""

    MAX_DETAILS_LENGTH: ClassVar[int] = 1200
    MEMORY_LIMIT: ClassVar[int] = 3

    _STRATEGY_HINTS: ClassVar[Mapping[FailureType, str]] = {
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

    @staticmethod
    def inject(
        test_result: TestResult,
        failure_type: FailureType,
        memory: MemoryRetriever,
    ) -> FeedbackMessage:
        failure = _select_failure(test_result, failure_type)
        return FeedbackMessage(
            failure_type=failure_type,
            details=_truncate(
                _format_details(test_result, failure_type, failure),
                FeedbackInjector.MAX_DETAILS_LENGTH,
            ),
            strategy_hint=FeedbackInjector._STRATEGY_HINTS[failure_type],
            relevant_memory=_retrieve_memory(memory, failure_type),
        )


def _select_failure(test_result: TestResult, failure_type: FailureType) -> Failure | None:
    for failure in test_result.failures:
        if failure.type == failure_type:
            return failure
    if test_result.failures:
        return test_result.failures[0]
    return None


def _format_details(
    test_result: TestResult,
    failure_type: FailureType,
    failure: Failure | None,
) -> str:
    lines = [
        f"failure_type: {failure_type.value}",
        f"status: {test_result.status}",
        f"summary: {_format_summary(test_result.summary)}",
    ]
    if failure is None:
        lines.append("failure: <not reported>")
        return "\n".join(lines)

    lines.extend(
        [
            f"test: {_format_value(failure.test_name)}",
            f"location: {_format_location(failure)}",
            f"expected: {_format_value(failure.expected)}",
            f"actual: {_format_value(failure.actual)}",
            f"message: {_format_value(failure.message)}",
        ]
    )
    return "\n".join(lines)


def _format_location(failure: Failure) -> str:
    if failure.file and failure.line:
        return f"{failure.file}:{failure.line}"
    if failure.file:
        return failure.file
    return "<not reported>"


def _format_summary(summary: Mapping[str, object]) -> str:
    if not summary:
        return "<empty>"
    return ", ".join(f"{key}={value}" for key, value in sorted(summary.items()))


def _format_value(value: str) -> str:
    return value if value else "<not reported>"


def _truncate(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 3].rstrip() + "..."


def _retrieve_memory(
    memory: MemoryRetriever,
    failure_type: FailureType,
) -> list[MemoryEntry]:
    try:
        return memory.retrieve_relevant(failure_type, limit=FeedbackInjector.MEMORY_LIMIT)
    except Exception:
        return []
