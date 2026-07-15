from __future__ import annotations

from dataclasses import is_dataclass
from datetime import datetime
from enum import Enum

from harness.models import (
    Action,
    Config,
    Failure,
    FailureType,
    FeedbackMessage,
    GuardResult,
    HITLRequest,
    HITLStatus,
    MemoryEntry,
    RoundOutcome,
    RoundRecord,
    StopReason,
    TestResult,
)


class TestEnums:
    def test_failure_type_values(self):
        assert FailureType.ASSERTION.value == "ASSERTION"
        assert FailureType.SYNTAX.value == "SYNTAX"
        assert FailureType.IMPORT.value == "IMPORT"
        assert FailureType.RUNTIME.value == "RUNTIME"
        assert FailureType.TIMEOUT.value == "TIMEOUT"
        assert FailureType.COLLECTION.value == "COLLECTION"
        assert len(FailureType) == 6

    def test_round_outcome_values(self):
        assert RoundOutcome.PASS.value == "PASS"
        assert RoundOutcome.FAIL.value == "FAIL"
        assert RoundOutcome.NO_TESTS.value == "NO_TESTS"
        assert RoundOutcome.HITL_DENIED.value == "HITL_DENIED"
        assert len(RoundOutcome) == 4

    def test_stop_reason_values(self):
        assert StopReason.PASS.value == "PASS"
        assert StopReason.MAX_ROUNDS.value == "MAX_ROUNDS"
        assert StopReason.STUCK.value == "STUCK"
        assert StopReason.HITL_DENIED.value == "HITL_DENIED"
        assert StopReason.LLM_ERROR.value == "LLM_ERROR"
        assert len(StopReason) == 5

    def test_hitl_status_values(self):
        assert HITLStatus.PENDING.value == "PENDING"
        assert HITLStatus.APPROVED.value == "APPROVED"
        assert HITLStatus.DENIED.value == "DENIED"
        assert HITLStatus.TIMEOUT.value == "TIMEOUT"
        assert len(HITLStatus) == 4

    def test_guard_result_values(self):
        assert GuardResult.ALLOW.value == "ALLOW"
        assert GuardResult.DENY.value == "DENY"
        assert GuardResult.PENDING.value == "PENDING"
        assert len(GuardResult) == 3

    def test_all_enums_are_enum_classes(self):
        assert issubclass(FailureType, Enum)
        assert issubclass(RoundOutcome, Enum)
        assert issubclass(StopReason, Enum)
        assert issubclass(HITLStatus, Enum)
        assert issubclass(GuardResult, Enum)


class TestConfig:
    def test_config_default_values(self):
        config = Config()
        assert config.max_rounds == 10
        assert config.target_directory == "./workspace"
        assert config.test_command == "pytest --json-report --output=.harness/report.json"
        assert config.model == "deepseek-chat"
        assert config.temperature == 0.1
        assert config.memory_file == ".harness/memory.json"
        assert config.hitl_timeout_seconds == 300
        assert config.llm_timeout == 60
        assert config.pytest_timeout == 60
        assert config.stuck_threshold == 3
        assert config.llm_retry_count == 3

    def test_config_default_enabled_tools(self):
        config = Config()
        assert config.enabled_tools == [
            "write_file",
            "read_file",
            "list_files",
            "run_tests",
            "run_command",
            "finish",
        ]

    def test_config_default_dangerous_command_patterns(self):
        config = Config()
        assert config.dangerous_command_patterns == [
            r"rm\s+-rf",
            r"git\s+push",
            r"sudo\s+",
            r"curl\s+|wget\s+",
            r"docker\s+",
        ]

    def test_config_custom_values(self):
        config = Config(
            max_rounds=5,
            target_directory="/tmp/test",
            test_command="pytest",
            model="gpt-4",
            temperature=0.5,
            memory_file="custom.json",
            enabled_tools=["write_file", "read_file"],
            dangerous_command_patterns=["rm"],
            hitl_timeout_seconds=60,
            llm_timeout=30,
            pytest_timeout=30,
            stuck_threshold=5,
            llm_retry_count=2,
        )
        assert config.max_rounds == 5
        assert config.target_directory == "/tmp/test"
        assert config.test_command == "pytest"
        assert config.model == "gpt-4"
        assert config.temperature == 0.5
        assert config.memory_file == "custom.json"
        assert config.enabled_tools == ["write_file", "read_file"]
        assert config.dangerous_command_patterns == ["rm"]
        assert config.hitl_timeout_seconds == 60
        assert config.llm_timeout == 30
        assert config.pytest_timeout == 30
        assert config.stuck_threshold == 5
        assert config.llm_retry_count == 2

    def test_config_field_types(self):
        config = Config()
        assert isinstance(config.max_rounds, int)
        assert isinstance(config.target_directory, str)
        assert isinstance(config.test_command, str)
        assert isinstance(config.model, str)
        assert isinstance(config.temperature, float)
        assert isinstance(config.memory_file, str)
        assert isinstance(config.enabled_tools, list)
        assert isinstance(config.dangerous_command_patterns, list)
        assert isinstance(config.hitl_timeout_seconds, int)
        assert isinstance(config.llm_timeout, int)
        assert isinstance(config.pytest_timeout, int)
        assert isinstance(config.stuck_threshold, int)
        assert isinstance(config.llm_retry_count, int)

    def test_config_is_dataclass(self):
        assert is_dataclass(Config)

    def test_config_mutable_defaults_isolated(self):
        """Two Config instances must not share mutable default lists."""
        c1 = Config()
        c2 = Config()
        assert c1.enabled_tools is not c2.enabled_tools
        assert c1.dangerous_command_patterns is not c2.dangerous_command_patterns
        c1.enabled_tools.append("extra_tool")
        assert "extra_tool" not in c2.enabled_tools


class TestAction:
    def test_action_instantiation(self):
        action = Action(
            tool_name="write_file",
            args={"path": "test.py", "content": "print('hello')"},
        )
        assert action.tool_name == "write_file"
        assert action.args == {"path": "test.py", "content": "print('hello')"}
        assert action.raw_tool_call is None

    def test_action_with_raw_tool_call(self):
        raw = {"id": "call_123", "type": "function"}
        action = Action(
            tool_name="run_tests",
            args={},
            raw_tool_call=raw,
        )
        assert action.tool_name == "run_tests"
        assert action.args == {}
        assert action.raw_tool_call == raw

    def test_action_is_dataclass(self):
        assert is_dataclass(Action)

    def test_action_field_types(self):
        action = Action(tool_name="test", args={})
        assert isinstance(action.tool_name, str)
        assert isinstance(action.args, dict)


class TestTestResult:
    def test_test_result_instantiation(self):
        result = TestResult(
            status="PASS",
            failures=[],
            summary={"total": 5, "passed": 5, "failed": 0},
        )
        assert result.status == "PASS"
        assert result.failures == []
        assert result.summary == {"total": 5, "passed": 5, "failed": 0}

    def test_test_result_with_failures(self):
        failure = Failure(
            type="ASSERTION",
            test_name="test_example",
            message="assert 1 == 2",
            file="test_example.py",
            line=10,
            expected="1",
            actual="2",
        )
        result = TestResult(
            status="FAIL",
            failures=[failure],
            summary={"total": 5, "passed": 4, "failed": 1},
        )
        assert result.status == "FAIL"
        assert len(result.failures) == 1
        assert result.failures[0].test_name == "test_example"

    def test_test_result_is_dataclass(self):
        assert is_dataclass(TestResult)

    def test_test_result_field_types(self):
        result = TestResult(status="PASS", failures=[], summary={})
        assert isinstance(result.status, str)
        assert isinstance(result.failures, list)
        assert isinstance(result.summary, dict)


class TestFailure:
    def test_failure_instantiation(self):
        failure = Failure(
            type="ASSERTION",
            test_name="test_add",
            message="assert 3 == 5",
            file="tests/test_math.py",
            line=15,
            expected="3",
            actual="5",
        )
        assert failure.type == "ASSERTION"
        assert failure.test_name == "test_add"
        assert failure.message == "assert 3 == 5"
        assert failure.file == "tests/test_math.py"
        assert failure.line == 15
        assert failure.expected == "3"
        assert failure.actual == "5"

    def test_failure_with_defaults(self):
        failure = Failure(
            type="RUNTIME",
            test_name="test_runtime",
            message="something went wrong",
            file="",
            line=0,
            expected="",
            actual="",
        )
        assert failure.type == "RUNTIME"
        assert failure.line == 0

    def test_failure_is_dataclass(self):
        assert is_dataclass(Failure)

    def test_failure_can_use_failure_type_enum(self):
        failure = Failure(
            type=FailureType.IMPORT.value,
            test_name="test_import",
            message="No module named 'foo'",
            file="test_foo.py",
            line=1,
            expected="",
            actual="",
        )
        assert failure.type == "IMPORT"
        assert FailureType(failure.type) == FailureType.IMPORT


class TestFeedbackMessage:
    def test_feedback_message_instantiation(self):
        feedback = FeedbackMessage(
            failure_type="ASSERTION",
            details="Test test_add failed: assert 3 == 5",
            strategy_hint="Check the expected and actual values.",
            relevant_memory=[],
        )
        assert feedback.failure_type == "ASSERTION"
        assert feedback.details == "Test test_add failed: assert 3 == 5"
        assert feedback.strategy_hint == "Check the expected and actual values."
        assert feedback.relevant_memory == []

    def test_feedback_message_with_memory(self):
        memory_entry = MemoryEntry(
            session_id="session-1",
            round=1,
            failure_type="ASSERTION",
            test_name="test_add",
            message="assert 3 == 5",
            strategy_used="fix_assertion",
            outcome="resolved",
        )
        feedback = FeedbackMessage(
            failure_type="ASSERTION",
            details="details here",
            strategy_hint="fix the assertion",
            relevant_memory=[memory_entry],
        )
        assert len(feedback.relevant_memory) == 1
        assert feedback.relevant_memory[0].session_id == "session-1"

    def test_feedback_message_is_dataclass(self):
        assert is_dataclass(FeedbackMessage)

    def test_feedback_message_field_types(self):
        feedback = FeedbackMessage(
            failure_type="ASSERTION",
            details="details",
            strategy_hint="hint",
            relevant_memory=[],
        )
        assert isinstance(feedback.failure_type, str)
        assert isinstance(feedback.details, str)
        assert isinstance(feedback.strategy_hint, str)
        assert isinstance(feedback.relevant_memory, list)


class TestRoundRecord:
    def test_round_record_instantiation(self):
        action = Action(tool_name="write_file", args={"path": "test.py", "content": ""})
        record = RoundRecord(
            round_number=1,
            actions=[action],
            failure_fingerprint="abc123",
            strategy_used="write_test",
            outcome=RoundOutcome.FAIL,
        )
        assert record.round_number == 1
        assert len(record.actions) == 1
        assert record.failure_fingerprint == "abc123"
        assert record.strategy_used == "write_test"
        assert record.outcome == RoundOutcome.FAIL

    def test_round_record_outcome_pass(self):
        record = RoundRecord(
            round_number=2,
            actions=[],
            failure_fingerprint="",
            strategy_used="",
            outcome=RoundOutcome.PASS,
        )
        assert record.outcome == RoundOutcome.PASS

    def test_round_record_outcome_fail(self):
        record = RoundRecord(
            round_number=3,
            actions=[],
            failure_fingerprint="",
            strategy_used="",
            outcome=RoundOutcome.FAIL,
        )
        assert record.outcome == RoundOutcome.FAIL

    def test_round_record_outcome_no_tests(self):
        record = RoundRecord(
            round_number=4,
            actions=[],
            failure_fingerprint="",
            strategy_used="",
            outcome=RoundOutcome.NO_TESTS,
        )
        assert record.outcome == RoundOutcome.NO_TESTS

    def test_round_record_outcome_hitl_denied(self):
        record = RoundRecord(
            round_number=5,
            actions=[],
            failure_fingerprint="",
            strategy_used="",
            outcome=RoundOutcome.HITL_DENIED,
        )
        assert record.outcome == RoundOutcome.HITL_DENIED

    def test_round_record_is_dataclass(self):
        assert is_dataclass(RoundRecord)

    def test_round_record_field_types(self):
        record = RoundRecord(
            round_number=1,
            actions=[],
            failure_fingerprint="",
            strategy_used="",
            outcome=RoundOutcome.FAIL,
        )
        assert isinstance(record.round_number, int)
        assert isinstance(record.actions, list)
        assert isinstance(record.failure_fingerprint, str)
        assert isinstance(record.strategy_used, str)
        assert isinstance(record.outcome, RoundOutcome)


class TestHITLRequest:
    def test_hitl_request_instantiation(self):
        action = Action(tool_name="run_command", args={"cmd": "rm -rf /tmp/test"})
        timestamp = datetime.now()
        hitl = HITLRequest(
            action=action,
            status=HITLStatus.PENDING,
            timestamp=timestamp,
            decision="",
        )
        assert hitl.action.tool_name == "run_command"
        assert hitl.status == HITLStatus.PENDING
        assert hitl.timestamp == timestamp
        assert hitl.decision == ""

    def test_hitl_request_approved(self):
        action = Action(tool_name="run_command", args={"cmd": "ls"})
        timestamp = datetime.now()
        hitl = HITLRequest(
            action=action,
            status=HITLStatus.APPROVED,
            timestamp=timestamp,
            decision="user approved",
        )
        assert hitl.status == HITLStatus.APPROVED
        assert hitl.decision == "user approved"

    def test_hitl_request_denied(self):
        action = Action(tool_name="run_command", args={"cmd": "rm -rf /"})
        timestamp = datetime.now()
        hitl = HITLRequest(
            action=action,
            status=HITLStatus.DENIED,
            timestamp=timestamp,
            decision="dangerous command denied",
        )
        assert hitl.status == HITLStatus.DENIED

    def test_hitl_request_timeout(self):
        action = Action(tool_name="run_command", args={"cmd": "sudo ls"})
        timestamp = datetime.now()
        hitl = HITLRequest(
            action=action,
            status=HITLStatus.TIMEOUT,
            timestamp=timestamp,
            decision="timeout",
        )
        assert hitl.status == HITLStatus.TIMEOUT

    def test_hitl_request_is_dataclass(self):
        assert is_dataclass(HITLRequest)

    def test_hitl_request_field_types(self):
        action = Action(tool_name="test", args={})
        hitl = HITLRequest(
            action=action,
            status=HITLStatus.PENDING,
            timestamp=datetime.now(),
            decision="",
        )
        assert isinstance(hitl.status, HITLStatus)
        assert isinstance(hitl.timestamp, datetime)
        assert isinstance(hitl.decision, str)


class TestMemoryEntry:
    def test_memory_entry_instantiation(self):
        entry = MemoryEntry(
            session_id="session-abc",
            round=1,
            failure_type="ASSERTION",
            test_name="test_add",
            message="assert 3 == 5",
            strategy_used="fix_assertion",
            outcome="resolved",
        )
        assert entry.session_id == "session-abc"
        assert entry.round == 1
        assert entry.failure_type == "ASSERTION"
        assert entry.test_name == "test_add"
        assert entry.message == "assert 3 == 5"
        assert entry.strategy_used == "fix_assertion"
        assert entry.outcome == "resolved"

    def test_memory_entry_unresolved(self):
        entry = MemoryEntry(
            session_id="session-xyz",
            round=2,
            failure_type="IMPORT",
            test_name="test_import",
            message="No module named 'foo'",
            strategy_used="add_import",
            outcome="unresolved",
        )
        assert entry.outcome == "unresolved"

    def test_memory_entry_is_dataclass(self):
        assert is_dataclass(MemoryEntry)

    def test_memory_entry_field_types(self):
        entry = MemoryEntry(
            session_id="s",
            round=1,
            failure_type="RUNTIME",
            test_name="t",
            message="m",
            strategy_used="s",
            outcome="resolved",
        )
        assert isinstance(entry.session_id, str)
        assert isinstance(entry.round, int)
        assert isinstance(entry.failure_type, str)
        assert isinstance(entry.test_name, str)
        assert isinstance(entry.message, str)
        assert isinstance(entry.strategy_used, str)
        assert isinstance(entry.outcome, str)
