from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from harness.feedback import FailureClassifier, FeedbackInjector, RoundTracker, TestResultParser
from harness.llm.base import LLMClient, LLMResponse, ToolCall
from harness.memory.retriever import MemoryRetriever
from harness.models import (
    Action,
    Config,
    Failure,
    FailureType,
    FeedbackMessage,
    RoundOutcome,
    RoundRecord,
    StopReason,
    TestResult,
)
from harness.tools.base import ToolRegistry, ToolResult


@dataclass
class AgentResult:
    status: StopReason
    rounds: list[RoundRecord]
    output_files: list[str]


class AgentLoop:
    """Coordinate LLM tool calls, feedback injection, and stop decisions."""

    def __init__(
        self,
        config: Config,
        llm_client: LLMClient,
        tool_registry: ToolRegistry,
        *,
        memory: MemoryRetriever | None = None,
    ) -> None:
        self.config = config
        self.llm_client = llm_client
        self.tool_registry = tool_registry
        self.memory = memory or MemoryRetriever(config.memory_file)
        self.tracker = RoundTracker(config.max_rounds, config.stuck_threshold)
        self.output_files: list[str] = []

    def run(self, requirement: str) -> AgentResult:
        messages = _initial_messages(requirement)

        for round_number in range(1, self.config.max_rounds + 1):
            response = self._chat_with_retries(messages)
            actions = [_action_from_tool_call(call) for call in response.tool_calls]
            if not actions:
                record = _round_record(
                    round_number,
                    actions,
                    RoundOutcome.PASS,
                    "",
                    "",
                )
                self.tracker.update(record)
                return self._result(StopReason.PASS)

            stop_reason: StopReason | None = None
            feedback: FeedbackMessage | None = None
            record = _round_record(round_number, actions, RoundOutcome.FAIL, "", "")

            for action in actions:
                if action.tool_name == "finish":
                    record = _round_record(
                        round_number,
                        actions,
                        RoundOutcome.PASS,
                        "",
                        "finish",
                    )
                    break

                tool_result = self._dispatch(action)
                if _requires_approval(tool_result):
                    record = _round_record(
                        round_number,
                        actions,
                        RoundOutcome.HITL_DENIED,
                        _tool_failure_fingerprint(action, tool_result),
                        "hitl_denied",
                    )
                    break

                self._record_output_file(action)
                if action.tool_name == "run_tests":
                    test_result = _test_result_from_tool_result(tool_result)
                    record, feedback = self._record_from_test_result(
                        round_number,
                        actions,
                        test_result,
                    )
                    break

                if not tool_result.success:
                    record = _round_record(
                        round_number,
                        actions,
                        RoundOutcome.FAIL,
                        _tool_failure_fingerprint(action, tool_result),
                        "tool_error",
                    )
                    break

            self.tracker.update(record)
            stop_reason = self.tracker.should_stop()
            if stop_reason is not None:
                return self._result(stop_reason)
            if feedback is not None:
                messages.append(_feedback_message(feedback))

        return self._result(StopReason.MAX_ROUNDS)

    def _chat_with_retries(self, messages: list[dict[str, Any]]) -> LLMResponse:
        attempts = self.config.llm_retry_count + 1
        last_exception: Exception | None = None
        for _ in range(attempts):
            try:
                return self.llm_client.chat(messages, self.tool_registry.get_schemas())
            except Exception as exc:
                last_exception = exc
        if last_exception is None:
            raise RuntimeError("LLM retry loop exited without an exception")
        raise last_exception

    def _dispatch(self, action: Action) -> ToolResult:
        try:
            return self.tool_registry.dispatch(action)
        except Exception as exc:
            return ToolResult(success=False, output={}, error=str(exc))

    def _record_output_file(self, action: Action) -> None:
        if action.tool_name != "write_file":
            return
        path = action.args.get("path")
        if isinstance(path, str):
            self.output_files.append(path)

    def _record_from_test_result(
        self,
        round_number: int,
        actions: list[Action],
        test_result: TestResult,
    ) -> tuple[RoundRecord, FeedbackMessage | None]:
        if test_result.status == "PASS":
            return (
                _round_record(round_number, actions, RoundOutcome.PASS, "", "tests_passed"),
                None,
            )

        failure_type = _classify_first_failure(test_result)
        feedback = FeedbackInjector.inject(test_result, failure_type, self.memory)
        fingerprint = ""
        if test_result.failures:
            fingerprint = RoundTracker.failure_fingerprint(test_result.failures[0])
        return (
            _round_record(
                round_number,
                actions,
                RoundOutcome.FAIL,
                fingerprint,
                feedback.strategy_hint,
            ),
            feedback,
        )

    def _result(self, status: StopReason) -> AgentResult:
        return AgentResult(
            status=status,
            rounds=list(self.tracker.history),
            output_files=list(self.output_files),
        )


def _initial_messages(requirement: str) -> list[dict[str, Any]]:
    return [
        {
            "role": "system",
            "content": "You are a TDD coding agent. Use tools and run tests.",
        },
        {"role": "user", "content": requirement},
    ]


def _feedback_message(feedback: FeedbackMessage) -> dict[str, Any]:
    return {
        "role": "user",
        "content": (
            f"{feedback.details}\n"
            f"strategy_hint: {feedback.strategy_hint}\n"
            f"relevant_memory: {feedback.relevant_memory}"
        ),
    }


def _action_from_tool_call(tool_call: ToolCall) -> Action:
    return Action(
        tool_name=tool_call.name,
        args=dict(tool_call.arguments),
        raw_tool_call=tool_call,
    )


def _requires_approval(tool_result: ToolResult) -> bool:
    return tool_result.output.get("status") == "PENDING"


def _test_result_from_tool_result(tool_result: ToolResult) -> TestResult:
    embedded_result = tool_result.output.get("test_result")
    if isinstance(embedded_result, TestResult):
        return embedded_result

    report_json = tool_result.output.get("report_json")
    if isinstance(report_json, str):
        return TestResultParser.parse(report_json)

    report_path = tool_result.output.get("report_path")
    if isinstance(report_path, str):
        try:
            return TestResultParser.parse(Path(report_path).read_text(encoding="utf-8"))
        except OSError as exc:
            return _runtime_error_result(str(exc))

    if tool_result.error is not None:
        return _runtime_error_result(tool_result.error)
    return _runtime_error_result("run_tests did not return a report")


def _classify_first_failure(test_result: TestResult) -> FailureType:
    if not test_result.failures:
        return FailureType.RUNTIME
    failure = test_result.failures[0]
    failure.type = FailureClassifier.classify(failure)
    return failure.type


def _round_record(
    round_number: int,
    actions: list[Action],
    outcome: RoundOutcome,
    fingerprint: str,
    strategy_used: str,
) -> RoundRecord:
    return RoundRecord(
        round_number=round_number,
        actions=actions,
        failure_fingerprint=fingerprint,
        strategy_used=strategy_used,
        outcome=outcome,
    )


def _tool_failure_fingerprint(action: Action, tool_result: ToolResult) -> str:
    return f"TOOL|{action.tool_name}|{tool_result.error or ''}"


def _runtime_error_result(message: str) -> TestResult:
    return TestResult(
        status="ERROR",
        failures=[
            Failure(
                type=FailureType.RUNTIME,
                test_name="run_tests",
                message=message,
                file="",
                line=0,
                expected="",
                actual="",
            )
        ],
        summary={},
    )
