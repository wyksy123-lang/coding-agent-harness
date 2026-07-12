from __future__ import annotations

import json
import re
from typing import Any

from harness.models import Failure, FailureType, TestResult

_ASSERT_PATTERN = re.compile(r"assert\s+(.+?)\s*==\s*(.+)")


class TestResultParser:
    @staticmethod
    def parse(json_str: str) -> TestResult:
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as exc:
            return TestResult(
                status="ERROR",
                failures=[
                    Failure(
                        type=FailureType.COLLECTION,
                        test_name="",
                        message=str(exc),
                        file="",
                        line=0,
                        expected="",
                        actual="",
                    )
                ],
                summary={},
            )

        exitcode = data.get("exitcode")
        if exitcode == 0:
            status = "PASS"
        elif exitcode == 1:
            status = "FAIL"
        else:
            status = "ERROR"

        failures: list[Failure] = []

        for test in data.get("tests", []):
            if test.get("outcome") != "failed":
                continue
            call = test.get("call", {})
            crash = call.get("crash", {})
            message = crash.get("message")
            if message is None:
                message = call.get("longrepr", "")
            file = crash.get("path", "")
            line = crash.get("lineno", 0)
            test_name = test.get("nodeid", "")
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

        for collector in data.get("collectors", []):
            if collector.get("outcome") != "failed":
                continue
            longrepr = collector.get("longrepr", "")
            if "SyntaxError" in longrepr:
                failure_type = FailureType.SYNTAX
            else:
                failure_type = FailureType.COLLECTION
            failures.append(
                Failure(
                    type=failure_type,
                    test_name=collector.get("nodeid", ""),
                    message=longrepr,
                    file="",
                    line=0,
                    expected="",
                    actual="",
                )
            )

        summary: dict[str, Any] = {**data.get("summary", {}), "exitcode": exitcode}

        return TestResult(
            status=status,
            failures=failures,
            summary=summary,
        )

    @staticmethod
    def _classify(message: str) -> FailureType:
        if "AssertionError" in message or "assert" in message:
            return FailureType.ASSERTION
        if "ModuleNotFoundError" in message or "ImportError" in message:
            return FailureType.IMPORT
        if "SyntaxError" in message or "IndentationError" in message:
            return FailureType.SYNTAX
        if (
            "TypeError" in message
            or "ValueError" in message
            or "KeyError" in message
            or "AttributeError" in message
        ):
            return FailureType.RUNTIME
        return FailureType.RUNTIME

    @staticmethod
    def _extract_expected_actual(message: str) -> tuple[str, str]:
        match = _ASSERT_PATTERN.search(message)
        if match:
            return match.group(2), match.group(1)
        return "", ""
