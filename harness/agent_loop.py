from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast

from harness.approval import ApprovalBroker
from harness.feedback import (
    FailureClassifier,
    FeedbackInjector,
    RoundTracker,
    TestResultParser,
)
from harness.governance.hitl import HITLState
from harness.llm.base import LLMClient, LLMResponse, ToolCall
from harness.memory.retriever import MemoryRecorder, MemoryRetriever
from harness.models import (
    Action,
    Config,
    Failure,
    FailureType,
    FeedbackMessage,
    HITLRequest,
    HITLStatus,
    RoundOutcome,
    RoundRecord,
    StopReason,
    TestResult,
)
from harness.run_events import (
    HITLDecision,
    RunEvent,
    RunEventType,
    RunPhase,
    TestStatus,
)
from harness.tools.base import ToolRegistry, ToolResult


class RoundRecorder(Protocol):
    def record(self, round_record: RoundRecord) -> None: ...


class RunEventSink(Protocol):
    def __call__(self, event: RunEvent) -> None: ...


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
        memory_recorder: RoundRecorder | None = None,
        hitl_state: HITLState | None = None,
        approval_broker: ApprovalBroker | None = None,
        event_sink: RunEventSink | None = None,
    ) -> None:
        self.config = config
        self.llm_client = llm_client
        self.tool_registry = tool_registry
        self.memory = memory or MemoryRetriever(config.memory_file)
        self.memory_recorder = memory_recorder or MemoryRecorder(config.memory_file)
        self.hitl_state = hitl_state or HITLState()
        self.approval_broker = approval_broker
        self.event_sink = event_sink
        self._run_id = "agent-run"
        self._event_index = 0
        self.tracker = RoundTracker(config.max_rounds, config.stuck_threshold)
        self.output_files: list[str] = []

    def run(self, requirement: str) -> AgentResult:
        self._emit(
            RunEventType.TASK_STARTED,
            phase=RunPhase.RUNNING,
            summary="Task started",
        )
        messages = _initial_messages(requirement)
        has_green_tests = False

        for round_number in range(1, self.config.max_rounds + 1):
            self._emit(
                RunEventType.ROUND_STARTED,
                round_index=round_number,
                phase=RunPhase.RUNNING,
                summary=f"Round {round_number} started",
            )
            response = self._chat_with_retries(messages)
            self._emit(
                RunEventType.MODEL_RESPONSE,
                round_index=round_number,
                phase=RunPhase.RUNNING,
                summary=response.finish_reason,
            )
            actions = [_action_from_tool_call(call) for call in response.tool_calls]
            if not actions:
                record = _round_record(
                    round_number,
                    actions,
                    RoundOutcome.FAIL,
                    _llm_failure_fingerprint(response),
                    "llm_no_tool_calls",
                )
                self.tracker.update(record)
                self._record_memory(record)
                stop_reason = self.tracker.should_stop()
                if stop_reason is not None:
                    return self._result(stop_reason)
                messages.append(
                    _plain_feedback_message("llm_no_tool_calls", response.content)
                )
                continue

            stop_reason = None
            feedback: FeedbackMessage | None = None
            plain_feedback: dict[str, Any] | None = None
            record = _round_record(round_number, actions, RoundOutcome.FAIL, "", "")

            for action in actions:
                self._emit(
                    RunEventType.TOOL_REQUESTED,
                    round_index=round_number,
                    phase=RunPhase.RUNNING,
                    tool_name=action.tool_name,
                    summary=action.tool_name,
                )
                if action.tool_name == "finish":
                    if has_green_tests:
                        tool_result = self._dispatch(action)
                        if tool_result.success:
                            record = _round_record(
                                round_number,
                                actions,
                                RoundOutcome.PASS,
                                "",
                                "finish",
                            )
                        else:
                            record = _round_record(
                                round_number,
                                actions,
                                RoundOutcome.FAIL,
                                _tool_failure_fingerprint(action, tool_result),
                                "tool_error",
                            )
                            plain_feedback = _plain_feedback_message(
                                "tool_error",
                                f"{action.tool_name}: "
                                f"{tool_result.error or 'tool failed'}",
                            )
                    else:
                        record = _round_record(
                            round_number,
                            actions,
                            RoundOutcome.FAIL,
                            _finish_before_green_fingerprint(action),
                            "finish_before_green",
                        )
                        plain_feedback = _plain_feedback_message(
                            "finish_before_green",
                            "Run the tests until they pass before calling finish.",
                        )
                    break

                if action.tool_name == "run_tests":
                    self._emit(
                        RunEventType.TESTS_STARTED,
                        round_index=round_number,
                        phase=RunPhase.TESTING,
                        tool_name=action.tool_name,
                        summary="Tests started",
                    )
                tool_result = self._dispatch(action)
                if _requires_approval(tool_result):
                    if self.approval_broker is None:
                        request = self.hitl_state.create(
                            action, self.config.hitl_timeout_seconds
                        )
                        record = _round_record(
                            round_number,
                            actions,
                            RoundOutcome.HITL_DENIED,
                            _hitl_failure_fingerprint(action, request.status.value),
                            "hitl_pending",
                        )
                        plain_feedback = _plain_feedback_message(
                            "hitl_pending",
                            f"Action {action.tool_name} requires human approval.",
                        )
                        break

                    request = self.approval_broker.request(
                        action,
                        self.config.hitl_timeout_seconds,
                    )
                    self._emit_hitl_events(round_number, action, request)
                    if request.status == HITLStatus.APPROVED:
                        tool_result = self._dispatch(action, approved=True)
                    else:
                        strategy = _hitl_strategy(request)
                        record = _round_record(
                            round_number,
                            actions,
                            RoundOutcome.FAIL,
                            _hitl_failure_fingerprint(action, request.status.value),
                            strategy,
                        )
                        plain_feedback = _plain_feedback_message(
                            strategy,
                            f"Action {action.tool_name} was not approved.",
                        )
                        break

                if action.tool_name == "run_tests":
                    test_result = _test_result_from_tool_result(tool_result)
                    self._emit(
                        RunEventType.TESTS_COMPLETED,
                        round_index=round_number,
                        phase=RunPhase.TESTING,
                        tool_name=action.tool_name,
                        test_status=_event_test_status(test_result),
                        summary=test_result.status,
                    )
                    has_green_tests = test_result.status == "PASS"
                    record, feedback = self._record_from_test_result(
                        round_number,
                        actions,
                        test_result,
                    )
                    if test_result.status == "PASS":
                        continue
                    break

                if not tool_result.success:
                    record = _round_record(
                        round_number,
                        actions,
                        RoundOutcome.FAIL,
                        _tool_failure_fingerprint(action, tool_result),
                        "tool_error",
                    )
                    plain_feedback = _plain_feedback_message(
                        "tool_error",
                        f"{action.tool_name}: {tool_result.error or 'tool failed'}",
                    )
                    break
                self._record_output_file(action)
                if _invalidates_green_tests(action):
                    has_green_tests = False

            self.tracker.update(record)
            self._record_memory(record)
            stop_reason = self.tracker.should_stop()
            if stop_reason is not None:
                return self._result(stop_reason)
            if feedback is not None:
                messages.append(_feedback_message(feedback))
            elif plain_feedback is not None:
                messages.append(plain_feedback)

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

    def _dispatch(self, action: Action, *, approved: bool = False) -> ToolResult:
        try:
            if approved:
                dispatch_approved = getattr(
                    self.tool_registry,
                    "dispatch_approved",
                    None,
                )
                if callable(dispatch_approved):
                    return cast(ToolResult, dispatch_approved(action))
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
                _round_record(
                    round_number,
                    actions,
                    RoundOutcome.PASS,
                    "",
                    "tests_passed",
                ),
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
        self._emit(
            RunEventType.RUN_FINISHED,
            phase=RunPhase.COMPLETED if status == StopReason.PASS else RunPhase.FAILED,
            stop_reason=status.value,
            summary=status.value,
        )
        return AgentResult(
            status=status,
            rounds=list(self.tracker.history),
            output_files=list(self.output_files),
        )

    def _record_memory(self, record: RoundRecord) -> None:
        self.memory_recorder.record(record)

    def _emit(
        self,
        event_type: RunEventType,
        *,
        round_index: int | None = None,
        phase: RunPhase | None = None,
        summary: str = "",
        tool_name: str | None = None,
        test_status: TestStatus | None = None,
        hitl_request_id: str | None = None,
        hitl_decision: HITLDecision | None = None,
        stop_reason: str | None = None,
    ) -> None:
        if self.event_sink is None:
            return
        self._event_index += 1
        self.event_sink(
            RunEvent(
                event_id=f"{self._run_id}-{self._event_index:04d}",
                run_id=self._run_id,
                event_type=event_type,
                round_index=round_index,
                phase=phase,
                summary=summary,
                tool_name=tool_name,
                test_status=test_status,
                hitl_request_id=hitl_request_id,
                hitl_decision=hitl_decision,
                stop_reason=stop_reason,
            )
        )

    def _emit_hitl_events(
        self,
        round_number: int,
        action: Action,
        request: HITLRequest,
    ) -> None:
        self._emit(
            RunEventType.HITL_REQUESTED,
            round_index=round_number,
            phase=RunPhase.AWAITING_APPROVAL,
            tool_name=action.tool_name,
            hitl_request_id=request.request_id,
            summary="Approval requested",
        )
        self._emit(
            RunEventType.HITL_RESOLVED,
            round_index=round_number,
            phase=RunPhase.RUNNING,
            tool_name=action.tool_name,
            hitl_request_id=request.request_id,
            hitl_decision=_event_hitl_decision(request),
            summary=request.status.value,
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


def _plain_feedback_message(kind: str, details: str) -> dict[str, Any]:
    return {
        "role": "user",
        "content": f"{kind}: {details}",
    }


def _action_from_tool_call(tool_call: ToolCall) -> Action:
    return Action(
        tool_name=tool_call.name,
        args=dict(tool_call.arguments),
        raw_tool_call=tool_call,
    )


def _requires_approval(tool_result: ToolResult) -> bool:
    return tool_result.output.get("status") == "PENDING"


def _event_test_status(test_result: TestResult) -> TestStatus:
    return {
        "PASS": TestStatus.PASSED,
        "FAIL": TestStatus.FAILED,
        "ERROR": TestStatus.ERROR,
    }.get(test_result.status, TestStatus.ERROR)


def _event_hitl_decision(request: HITLRequest) -> HITLDecision | None:
    if request.status == HITLStatus.APPROVED:
        return HITLDecision.APPROVED
    if request.status in {HITLStatus.DENIED, HITLStatus.TIMEOUT}:
        return HITLDecision.DENIED
    return None


def _hitl_strategy(request: HITLRequest) -> str:
    if request.status == HITLStatus.TIMEOUT:
        return "hitl_timeout"
    return "hitl_denied"


def _invalidates_green_tests(action: Action) -> bool:
    return action.tool_name in {"write_file", "run_command"}


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


def _hitl_failure_fingerprint(action: Action, decision: str) -> str:
    return f"HITL|{action.tool_name}|{decision}"


def _llm_failure_fingerprint(response: LLMResponse) -> str:
    return f"LLM|no_tool_calls|{response.finish_reason}:{response.content}"


def _finish_before_green_fingerprint(action: Action) -> str:
    return f"FINISH|before_green|{action.args.get('reason', '')}"


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
