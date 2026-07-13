from __future__ import annotations

from typing import cast

from harness.feedback.classifier import FailureClassifier
from harness.models import Failure, FailureType


def _failure(message: str) -> Failure:
    return Failure(
        type=FailureType.RUNTIME,
        test_name="tests/test_sample.py::test_example",
        message=message,
        file="tests/test_sample.py",
        line=1,
        expected="",
        actual="",
    )


class TestFailureClassifierExistence:
    def test_classifier_is_class(self):
        assert isinstance(FailureClassifier, type)

    def test_classifier_has_classify_method(self):
        assert hasattr(FailureClassifier, "classify")

    def test_classify_is_callable(self):
        assert callable(FailureClassifier.classify)


class TestFailureClassifierPatterns:
    def test_assertion_error_message_returns_assertion(self):
        failure = _failure("AssertionError: assert 1 == 2")

        result = FailureClassifier.classify(failure)

        assert result == FailureType.ASSERTION

    def test_syntax_error_message_returns_syntax(self):
        failure = _failure("SyntaxError: invalid syntax")

        result = FailureClassifier.classify(failure)

        assert result == FailureType.SYNTAX

    def test_import_error_message_returns_import(self):
        failure = _failure("ModuleNotFoundError: No module named 'missing_pkg'")

        result = FailureClassifier.classify(failure)

        assert result == FailureType.IMPORT

    def test_runtime_error_message_returns_runtime(self):
        failure = _failure("TypeError: unsupported operand type(s) for +")

        result = FailureClassifier.classify(failure)

        assert result == FailureType.RUNTIME

    def test_timeout_message_returns_timeout(self):
        failure = _failure("TimeoutExpired: process timed out after 60 seconds")

        result = FailureClassifier.classify(failure)

        assert result == FailureType.TIMEOUT

    def test_collection_failure_message_returns_collection(self):
        failure = _failure("ERROR collecting tests/test_sample.py\ncollected 0 items")

        result = FailureClassifier.classify(failure)

        assert result == FailureType.COLLECTION


class TestFailureClassifierDefaults:
    def test_unknown_message_defaults_to_runtime(self):
        failure = _failure("custom domain failure without known classifier keywords")

        result = FailureClassifier.classify(failure)

        assert result == FailureType.RUNTIME

    def test_empty_message_defaults_to_runtime(self):
        failure = _failure("")

        result = FailureClassifier.classify(failure)

        assert result == FailureType.RUNTIME


class TestFailureClassifierPrecedence:
    def test_syntax_error_with_assert_source_line_returns_syntax(self):
        failure = _failure("SyntaxError: invalid syntax\n    assert = 1")

        result = FailureClassifier.classify(failure)

        assert result == FailureType.SYNTAX

    def test_assertion_error_still_returns_assertion_when_message_mentions_syntax(self):
        failure = _failure("AssertionError: assert result == 'SyntaxError'")

        result = FailureClassifier.classify(failure)

        assert result == FailureType.ASSERTION


class TestFailureClassifierMalformedInputs:
    def test_none_message_defaults_to_runtime(self):
        failure = _failure(cast(str, None))

        result = FailureClassifier.classify(failure)

        assert result == FailureType.RUNTIME
