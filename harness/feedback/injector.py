from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import ClassVar

from harness.memory.retriever import MemoryRetriever
from harness.models import Failure, FailureType, FeedbackMessage, MemoryEntry, TestResult

logger = logging.getLogger(__name__)


class FeedbackInjector:
    """Build structured feedback from test failures and relevant memory."""

    MAX_DETAILS_LENGTH: ClassVar[int] = 1200
    MEMORY_LIMIT: ClassVar[int] = 3
    MAX_SUMMARY_LENGTH: ClassVar[int] = 160
    MAX_TEST_NAME_LENGTH: ClassVar[int] = 180
    MAX_LOCATION_LENGTH: ClassVar[int] = 160
    MAX_EXPECTED_LENGTH: ClassVar[int] = 220
    MAX_ACTUAL_LENGTH: ClassVar[int] = 220
    MAX_MESSAGE_LENGTH: ClassVar[int] = 420

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
            details=_truncate_details(
                _format_details(test_result, failure_type, failure)
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
            "test: "
            f"{_format_value(failure.test_name, FeedbackInjector.MAX_TEST_NAME_LENGTH)}",
            f"location: {_format_location(failure)}",
            "expected: "
            f"{_format_value(failure.expected, FeedbackInjector.MAX_EXPECTED_LENGTH)}",
            f"actual: {_format_value(failure.actual, FeedbackInjector.MAX_ACTUAL_LENGTH)}",
            f"message: {_format_value(failure.message, FeedbackInjector.MAX_MESSAGE_LENGTH)}",
        ]
    )
    return "\n".join(lines)


def _format_location(failure: Failure) -> str:
    if failure.file and failure.line:
        return _format_value(
            f"{failure.file}:{failure.line}",
            FeedbackInjector.MAX_LOCATION_LENGTH,
        )
    if failure.file:
        return _format_value(failure.file, FeedbackInjector.MAX_LOCATION_LENGTH)
    return "<not reported>"


def _format_summary(summary: Mapping[str, object]) -> str:
    if not summary:
        return "<empty>"
    return _format_value(
        ", ".join(f"{key}={value}" for key, value in sorted(summary.items())),
        FeedbackInjector.MAX_SUMMARY_LENGTH,
    )


def _format_value(value: str, max_length: int) -> str:
    if not value:
        return "<not reported>"
    return _truncate_value(value, max_length)


def _truncate_value(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 3].rstrip() + "..."


def _truncate_details(text: str) -> str:
    return _truncate_value(text, FeedbackInjector.MAX_DETAILS_LENGTH)


def _retrieve_memory(
    memory: MemoryRetriever,
    failure_type: FailureType,
) -> list[MemoryEntry]:
    try:
        return memory.retrieve_relevant(failure_type, limit=FeedbackInjector.MEMORY_LIMIT)
    except Exception as exc:
        logger.warning("Failed to retrieve memory for %s: %s", failure_type.value, exc)
        return []
