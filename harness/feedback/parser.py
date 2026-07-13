from __future__ import annotations

import json
import re
from typing import Any

from harness.models import Failure, FailureType, TestResult

_ASSERT_PATTERN = re.compile(r"assert\s+(.+?)\s*==\s*(.+)")


class TestResultParser:
    """Parse pytest ``--json-report`` output into a :class:`TestResult`.

    See SPEC §3.3.1 for the full specification.
    """

    @staticmethod
    def parse(json_str: str) -> TestResult:
        """Parse a pytest JSON report string into a :class:`TestResult`.

        Args:
            json_str: Raw JSON string from ``pytest --json-report``.

        Returns:
            A :class:`TestResult` with status, failures, and summary.
            On JSON parse failure, returns ``status="ERROR"`` with a
            single :class:`Failure` of ``type=COLLECTION``.
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as exc:
            return TestResultParser._error_result(str(exc))

        if not isinstance(data, dict):
            return TestResultParser._error_result("JSON root is not an object")

        exitcode = data.get("exitcode")
        if exitcode == 0:
            status = "PASS"
        elif exitcode == 1:
            status = "FAIL"
        else:
            status = "ERROR"

        failures: list[Failure] = []

        tests = data.get("tests", [])
        if isinstance(tests, list):
            for test in tests:
                if not isinstance(test, dict) or test.get("outcome") != "failed":
                    continue
                call = test.get("call") or {}
                crash = call.get("crash") or {}
                message = crash.get("message")
                if not message:
                    message = call.get("longrepr") or ""
                file = crash.get("path") or ""
                line = crash.get("lineno") or 0
                test_name = test.get("nodeid") or ""
                failure_type = TestResultParser._classify(message)
                expected, actual = TestResultParser._extract_expected_actual(message)
                failures.append(
                    Failure(
                        type=failure_type,
                        test_name=test_name,
                        message=message,
                        file=file,
                        line=line,
                        expected=expected,
                        actual=actual,
                    )
                )

        collectors = data.get("collectors", [])
        if isinstance(collectors, list):
            for collector in collectors:
                if not isinstance(collector, dict) or collector.get("outcome") != "failed":
                    continue
                longrepr = collector.get("longrepr") or ""
                failure_type = TestResultParser._classify(longrepr)
                failures.append(
                    Failure(
                        type=failure_type,
                        test_name=collector.get("nodeid") or "",
                        message=longrepr,
                        file="",
                        line=0,
                        expected="",
                        actual="",
                    )
                )

        summary: dict[str, Any] = {
            **(data.get("summary") or {}),
            "exitcode": exitcode,
        }

        return TestResult(
            status=status,
            failures=failures,
            summary=summary,
        )

    @staticmethod
    def _error_result(message: str) -> TestResult:
        """Build an ERROR TestResult for parse-level failures."""
        return TestResult(
            status="ERROR",
            failures=[
                Failure(
                    type=FailureType.COLLECTION,
                    test_name="",
                    message=message,
                    file="",
                    line=0,
                    expected="",
                    actual="",
                )
            ],
            summary={},
        )

    @staticmethod
    def _classify(message: str) -> FailureType:
        """Classify a failure message into a :class:`FailureType`.

        Uses the pattern-matching rules from SPEC §3.3.2.
        Defaults to :attr:`FailureType.RUNTIME` when no pattern matches.

        This is a *preliminary* classification used to fill the required
        ``Failure.type`` field.  T13 (FailureClassifier) will provide the
        authoritative public classifier.
        """
        if "AssertionError" in message or "assert" in message:
            return FailureType.ASSERTION
        if "SyntaxError" in message or "IndentationError" in message:
            return FailureType.SYNTAX
        if "ModuleNotFoundError" in message or "ImportError" in message:
            return FailureType.IMPORT
        return FailureType.RUNTIME

    @staticmethod
    def _extract_expected_actual(message: str) -> tuple[str, str]:
        """Extract expected and actual values from an assertion message.

        For ``assert X == Y``, returns ``(expected="Y", actual="X")``.
        Returns empty strings when the pattern does not match.
        """
        match = _ASSERT_PATTERN.search(message)
        if match:
            return match.group(2), match.group(1)
        return "", ""
