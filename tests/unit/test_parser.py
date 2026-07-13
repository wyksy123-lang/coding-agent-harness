from __future__ import annotations

import json
from dataclasses import is_dataclass
from pathlib import Path

from harness.feedback.parser import TestResultParser
from harness.models import Failure, FailureType, TestResult

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def _load_fixture(name: str) -> str:
    """Read a fixture file and return its raw text content."""
    return (FIXTURES_DIR / name).read_text()


def _load_fixture_json(name: str) -> dict:
    """Read a fixture file and return parsed JSON."""
    with open(FIXTURES_DIR / name) as f:
        return json.load(f)


class TestTestResultParserExistence:
    def test_parser_is_class(self):
        assert isinstance(TestResultParser, type)

    def test_parser_has_parse_method(self):
        assert hasattr(TestResultParser, "parse")

    def test_parse_is_callable(self):
        assert callable(TestResultParser.parse)

    def test_parser_can_be_instantiated(self):
        parser = TestResultParser()
        assert parser is not None

    def test_parse_is_instance_method(self):
        parser = TestResultParser()
        assert callable(parser.parse)


class TestParseAllPassed:
    def test_status_is_pass(self):
        result = TestResultParser.parse(_load_fixture("all_passed.json"))
        assert result.status == "PASS"

    def test_failures_is_empty(self):
        result = TestResultParser.parse(_load_fixture("all_passed.json"))
        assert result.failures == []

    def test_summary_has_passed_count(self):
        result = TestResultParser.parse(_load_fixture("all_passed.json"))
        assert result.summary.get("passed") == 2

    def test_summary_has_total_count(self):
        result = TestResultParser.parse(_load_fixture("all_passed.json"))
        assert result.summary.get("total") == 2

    def test_summary_has_collected_count(self):
        result = TestResultParser.parse(_load_fixture("all_passed.json"))
        assert result.summary.get("collected") == 2

    def test_exitcode_in_summary(self):
        result = TestResultParser.parse(_load_fixture("all_passed.json"))
        assert result.summary.get("exitcode") == 0


class TestParseAssertionFailure:
    def test_status_is_fail(self):
        result = TestResultParser.parse(_load_fixture("assertion_failure.json"))
        assert result.status == "FAIL"

    def test_failures_has_one_entry(self):
        result = TestResultParser.parse(_load_fixture("assertion_failure.json"))
        assert len(result.failures) == 1

    def test_failure_test_name(self):
        result = TestResultParser.parse(_load_fixture("assertion_failure.json"))
        failure = result.failures[0]
        assert failure.test_name == "test_sample.py::test_assertion_fail"

    def test_failure_message_contains_assert(self):
        result = TestResultParser.parse(_load_fixture("assertion_failure.json"))
        failure = result.failures[0]
        assert "assert" in failure.message.lower()

    def test_failure_file(self):
        result = TestResultParser.parse(_load_fixture("assertion_failure.json"))
        failure = result.failures[0]
        assert failure.file == "/tmp/test_sample.py"

    def test_failure_line(self):
        result = TestResultParser.parse(_load_fixture("assertion_failure.json"))
        failure = result.failures[0]
        assert failure.line == 5

    def test_failure_type_is_failure_type(self):
        result = TestResultParser.parse(_load_fixture("assertion_failure.json"))
        failure = result.failures[0]
        assert isinstance(failure.type, FailureType)

    def test_failure_type_is_assertion(self):
        result = TestResultParser.parse(_load_fixture("assertion_failure.json"))
        failure = result.failures[0]
        assert failure.type == FailureType.ASSERTION

    def test_summary_has_failed_count(self):
        result = TestResultParser.parse(_load_fixture("assertion_failure.json"))
        assert result.summary.get("failed") == 1


class TestParseImportError:
    def test_status_is_fail(self):
        result = TestResultParser.parse(_load_fixture("import_error.json"))
        assert result.status == "FAIL"

    def test_failures_has_one_entry(self):
        result = TestResultParser.parse(_load_fixture("import_error.json"))
        assert len(result.failures) == 1

    def test_failure_message_contains_modulenotfounderror(self):
        result = TestResultParser.parse(_load_fixture("import_error.json"))
        failure = result.failures[0]
        assert "ModuleNotFoundError" in failure.message

    def test_failure_test_name(self):
        result = TestResultParser.parse(_load_fixture("import_error.json"))
        failure = result.failures[0]
        assert failure.test_name == "test_import.py::test_import_error"

    def test_failure_type_is_import(self):
        result = TestResultParser.parse(_load_fixture("import_error.json"))
        failure = result.failures[0]
        assert failure.type == FailureType.IMPORT

    def test_failure_file(self):
        result = TestResultParser.parse(_load_fixture("import_error.json"))
        failure = result.failures[0]
        assert failure.file == "/tmp/test_import.py"

    def test_failure_line(self):
        result = TestResultParser.parse(_load_fixture("import_error.json"))
        failure = result.failures[0]
        assert failure.line == 5


class TestParseSyntaxError:
    def test_status_is_error(self):
        result = TestResultParser.parse(_load_fixture("syntax_error.json"))
        assert result.status == "ERROR"

    def test_failures_has_one_entry(self):
        result = TestResultParser.parse(_load_fixture("syntax_error.json"))
        assert len(result.failures) == 1

    def test_failure_type_is_syntax(self):
        result = TestResultParser.parse(_load_fixture("syntax_error.json"))
        failure = result.failures[0]
        assert failure.type == FailureType.SYNTAX

    def test_failure_message_contains_syntaxerror(self):
        result = TestResultParser.parse(_load_fixture("syntax_error.json"))
        failure = result.failures[0]
        assert "SyntaxError" in failure.message

    def test_summary_exitcode_is_two(self):
        result = TestResultParser.parse(_load_fixture("syntax_error.json"))
        assert result.summary.get("exitcode") == 2


class TestParseTypeError:
    def test_status_is_fail(self):
        result = TestResultParser.parse(_load_fixture("type_error.json"))
        assert result.status == "FAIL"

    def test_failures_has_one_entry(self):
        result = TestResultParser.parse(_load_fixture("type_error.json"))
        assert len(result.failures) == 1

    def test_failure_message_contains_valueerror(self):
        result = TestResultParser.parse(_load_fixture("type_error.json"))
        failure = result.failures[0]
        assert "ValueError" in failure.message

    def test_failure_test_name(self):
        result = TestResultParser.parse(_load_fixture("type_error.json"))
        failure = result.failures[0]
        assert failure.test_name == "test_type.py::test_value_error"

    def test_failure_type_is_runtime(self):
        result = TestResultParser.parse(_load_fixture("type_error.json"))
        failure = result.failures[0]
        assert failure.type == FailureType.RUNTIME

    def test_failure_file(self):
        result = TestResultParser.parse(_load_fixture("type_error.json"))
        failure = result.failures[0]
        assert failure.file == "/tmp/test_type.py"

    def test_failure_line(self):
        result = TestResultParser.parse(_load_fixture("type_error.json"))
        failure = result.failures[0]
        assert failure.line == 8


class TestParseMixedResults:
    def test_status_is_fail(self):
        result = TestResultParser.parse(_load_fixture("mixed_results.json"))
        assert result.status == "FAIL"

    def test_failures_has_two_entries(self):
        result = TestResultParser.parse(_load_fixture("mixed_results.json"))
        assert len(result.failures) == 2

    def test_summary_passed_count(self):
        result = TestResultParser.parse(_load_fixture("mixed_results.json"))
        assert result.summary.get("passed") == 2

    def test_summary_failed_count(self):
        result = TestResultParser.parse(_load_fixture("mixed_results.json"))
        assert result.summary.get("failed") == 2

    def test_summary_total_count(self):
        result = TestResultParser.parse(_load_fixture("mixed_results.json"))
        assert result.summary.get("total") == 4

    def test_first_failure_test_name(self):
        result = TestResultParser.parse(_load_fixture("mixed_results.json"))
        test_names = [f.test_name for f in result.failures]
        assert "test_mixed.py::test_assertion_fail" in test_names

    def test_second_failure_test_name(self):
        result = TestResultParser.parse(_load_fixture("mixed_results.json"))
        test_names = [f.test_name for f in result.failures]
        assert "test_mixed.py::test_import_fail" in test_names


class TestParseEmptyReport:
    def test_status_is_pass(self):
        result = TestResultParser.parse(_load_fixture("empty_report.json"))
        assert result.status == "PASS"

    def test_failures_is_empty(self):
        result = TestResultParser.parse(_load_fixture("empty_report.json"))
        assert result.failures == []

    def test_summary_total_is_zero(self):
        result = TestResultParser.parse(_load_fixture("empty_report.json"))
        assert result.summary.get("total") == 0


class TestParseInvalidJSON:
    def test_status_is_error(self):
        result = TestResultParser.parse("{ this is not valid json")
        assert result.status == "ERROR"

    def test_failures_has_one_entry(self):
        result = TestResultParser.parse("{ this is not valid json")
        assert len(result.failures) == 1

    def test_failure_type_is_collection(self):
        result = TestResultParser.parse("{ this is not valid json")
        failure = result.failures[0]
        assert failure.type == FailureType.COLLECTION

    def test_failure_message_is_non_empty(self):
        result = TestResultParser.parse("{ this is not valid json")
        failure = result.failures[0]
        assert failure.message != ""

    def test_returns_test_result_instance(self):
        result = TestResultParser.parse("{ this is not valid json")
        assert isinstance(result, TestResult)

    def test_summary_is_dict(self):
        result = TestResultParser.parse("{ this is not valid json")
        assert isinstance(result.summary, dict)


class TestParseEmptyString:
    def test_status_is_error(self):
        result = TestResultParser.parse("")
        assert result.status == "ERROR"

    def test_failure_type_is_collection(self):
        result = TestResultParser.parse("")
        failure = result.failures[0]
        assert failure.type == FailureType.COLLECTION

    def test_failures_has_one_entry(self):
        result = TestResultParser.parse("")
        assert len(result.failures) == 1

    def test_returns_test_result_instance(self):
        result = TestResultParser.parse("")
        assert isinstance(result, TestResult)


class TestParseMissingFields:
    def test_no_crash_on_missing_call(self):
        json_str = json.dumps(
            {
                "exitcode": 1,
                "summary": {"total": 1, "collected": 1},
                "tests": [
                    {"nodeid": "test_x.py::test_a", "outcome": "failed"}
                ],
            }
        )
        result = TestResultParser.parse(json_str)
        assert isinstance(result, TestResult)

    def test_missing_call_fills_defaults(self):
        json_str = json.dumps(
            {
                "exitcode": 1,
                "summary": {"total": 1, "collected": 1},
                "tests": [
                    {"nodeid": "test_x.py::test_a", "outcome": "failed"}
                ],
            }
        )
        result = TestResultParser.parse(json_str)
        assert len(result.failures) == 1
        failure = result.failures[0]
        assert failure.test_name == "test_x.py::test_a"

    def test_missing_crash_fills_default_line(self):
        json_str = json.dumps(
            {
                "exitcode": 1,
                "summary": {"total": 1, "collected": 1},
                "tests": [
                    {
                        "nodeid": "test_x.py::test_a",
                        "outcome": "failed",
                        "call": {"outcome": "failed"},
                    }
                ],
            }
        )
        result = TestResultParser.parse(json_str)
        failure = result.failures[0]
        assert failure.line == 0

    def test_missing_crash_fills_default_file(self):
        json_str = json.dumps(
            {
                "exitcode": 1,
                "summary": {"total": 1, "collected": 1},
                "tests": [
                    {
                        "nodeid": "test_x.py::test_a",
                        "outcome": "failed",
                        "call": {"outcome": "failed"},
                    }
                ],
            }
        )
        result = TestResultParser.parse(json_str)
        failure = result.failures[0]
        assert failure.file == ""

    def test_missing_summary_uses_empty_dict(self):
        json_str = json.dumps(
            {
                "exitcode": 0,
                "tests": [],
            }
        )
        result = TestResultParser.parse(json_str)
        assert isinstance(result.summary, dict)

    def test_missing_tests_key_no_crash(self):
        json_str = json.dumps(
            {
                "exitcode": 0,
                "summary": {"total": 0, "collected": 0},
            }
        )
        result = TestResultParser.parse(json_str)
        assert isinstance(result, TestResult)
        assert result.failures == []


class TestParseReturnType:
    def test_parse_returns_test_result_instance(self):
        result = TestResultParser.parse(_load_fixture("all_passed.json"))
        assert isinstance(result, TestResult)

    def test_failures_are_failure_instances(self):
        result = TestResultParser.parse(_load_fixture("assertion_failure.json"))
        for failure in result.failures:
            assert isinstance(failure, Failure)

    def test_summary_is_dict(self):
        result = TestResultParser.parse(_load_fixture("all_passed.json"))
        assert isinstance(result.summary, dict)

    def test_status_is_string(self):
        result = TestResultParser.parse(_load_fixture("all_passed.json"))
        assert isinstance(result.status, str)

    def test_failure_is_dataclass(self):
        result = TestResultParser.parse(_load_fixture("assertion_failure.json"))
        for failure in result.failures:
            assert is_dataclass(failure)

    def test_test_result_is_dataclass(self):
        result = TestResultParser.parse(_load_fixture("all_passed.json"))
        assert is_dataclass(result)


class TestParseExpectedActual:
    def test_expected_value_extracted(self):
        result = TestResultParser.parse(_load_fixture("assertion_failure.json"))
        failure = result.failures[0]
        assert failure.expected == "2"

    def test_actual_value_extracted(self):
        result = TestResultParser.parse(_load_fixture("assertion_failure.json"))
        failure = result.failures[0]
        assert failure.actual == "1"

    def test_expected_actual_from_mixed_results(self):
        result = TestResultParser.parse(_load_fixture("mixed_results.json"))
        assertion_failure = next(
            f for f in result.failures if "assertion" in f.test_name
        )
        assert assertion_failure.expected == "5"
        assert assertion_failure.actual == "3"

    def test_expected_empty_for_non_assertion(self):
        result = TestResultParser.parse(_load_fixture("import_error.json"))
        failure = result.failures[0]
        assert failure.expected == ""

    def test_actual_empty_for_non_assertion(self):
        result = TestResultParser.parse(_load_fixture("import_error.json"))
        failure = result.failures[0]
        assert failure.actual == ""

    def test_expected_actual_are_strings(self):
        result = TestResultParser.parse(_load_fixture("assertion_failure.json"))
        failure = result.failures[0]
        assert isinstance(failure.expected, str)
        assert isinstance(failure.actual, str)


class TestParseEdgeCases:
    """Edge cases identified during Code Quality Review."""

    def test_non_dict_json_list_returns_error(self):
        result = TestResultParser.parse("[1, 2, 3]")
        assert result.status == "ERROR"
        assert result.failures[0].type == FailureType.COLLECTION

    def test_non_dict_json_scalar_returns_error(self):
        result = TestResultParser.parse("42")
        assert result.status == "ERROR"
        assert result.failures[0].type == FailureType.COLLECTION

    def test_non_dict_json_string_returns_error(self):
        result = TestResultParser.parse('"hello"')
        assert result.status == "ERROR"
        assert result.failures[0].type == FailureType.COLLECTION

    def test_null_longrepr_in_test_does_not_crash(self):
        json_str = json.dumps(
            {
                "exitcode": 1,
                "summary": {"total": 1, "collected": 1},
                "tests": [
                    {
                        "nodeid": "test_x.py::test_a",
                        "outcome": "failed",
                        "call": {"outcome": "failed", "longrepr": None},
                    }
                ],
            }
        )
        result = TestResultParser.parse(json_str)
        assert result.status == "FAIL"
        assert len(result.failures) == 1
        assert result.failures[0].message == ""

    def test_null_longrepr_in_collector_does_not_crash(self):
        json_str = json.dumps(
            {
                "exitcode": 2,
                "summary": {"total": 0, "collected": 0},
                "collectors": [
                    {"nodeid": "test_x.py", "outcome": "failed", "longrepr": None}
                ],
            }
        )
        result = TestResultParser.parse(json_str)
        assert result.status == "ERROR"
        assert len(result.failures) == 1
        assert result.failures[0].message == ""

    def test_null_crash_message_falls_back_to_longrepr(self):
        json_str = json.dumps(
            {
                "exitcode": 1,
                "summary": {"total": 1, "collected": 1},
                "tests": [
                    {
                        "nodeid": "test_x.py::test_a",
                        "outcome": "failed",
                        "call": {
                            "outcome": "failed",
                            "crash": {"path": "/tmp/x.py", "lineno": 3, "message": None},
                            "longrepr": "fallback message with ValueError",
                        },
                    }
                ],
            }
        )
        result = TestResultParser.parse(json_str)
        failure = result.failures[0]
        assert "fallback message" in failure.message
        assert failure.type == FailureType.RUNTIME

    def test_tests_field_non_list_does_not_crash(self):
        json_str = json.dumps(
            {
                "exitcode": 0,
                "summary": {"total": 0, "collected": 0},
                "tests": "not a list",
            }
        )
        result = TestResultParser.parse(json_str)
        assert isinstance(result, TestResult)
        assert result.failures == []

    def test_collectors_field_non_list_does_not_crash(self):
        json_str = json.dumps(
            {
                "exitcode": 0,
                "summary": {"total": 0, "collected": 0},
                "collectors": "not a list",
            }
        )
        result = TestResultParser.parse(json_str)
        assert isinstance(result, TestResult)
        assert result.failures == []

    def test_test_entry_non_dict_skipped(self):
        json_str = json.dumps(
            {
                "exitcode": 1,
                "summary": {"total": 1, "collected": 1},
                "tests": ["not a dict"],
            }
        )
        result = TestResultParser.parse(json_str)
        assert result.failures == []

    def test_null_summary_uses_empty_dict(self):
        json_str = json.dumps(
            {
                "exitcode": 0,
                "summary": None,
                "tests": [],
            }
        )
        result = TestResultParser.parse(json_str)
        assert isinstance(result.summary, dict)
        assert result.summary.get("exitcode") == 0
