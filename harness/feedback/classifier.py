from __future__ import annotations

import re

from harness.models import Failure, FailureType

_ASSERT_KEYWORD_PATTERN = re.compile(r"\bassert\b")


class FailureClassifier:
    """Classify pytest failures using SPEC §3.3.2 pattern rules."""

    @staticmethod
    def classify(failure: Failure) -> FailureType:
        """Return the failure type matched by message/traceback text."""
        message = failure.message if isinstance(failure.message, str) else ""
        if "AssertionError" in message:
            return FailureType.ASSERTION
        if "SyntaxError" in message or "IndentationError" in message:
            return FailureType.SYNTAX
        if "ModuleNotFoundError" in message or "ImportError" in message:
            return FailureType.IMPORT
        if "timeout" in message.lower() or "TimeoutExpired" in message:
            return FailureType.TIMEOUT
        if "collecting" in message or "collected 0 items" in message:
            return FailureType.COLLECTION
        if _ASSERT_KEYWORD_PATTERN.search(message):
            return FailureType.ASSERTION
        return FailureType.RUNTIME
