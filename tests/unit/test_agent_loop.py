from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from harness.agent_loop import AgentLoop
from harness.llm.base import LLMClient, LLMResponse, ToolCall
from harness.models import Config, HITLRequest, HITLStatus, StopReason
from harness.run_events import RunEventType
from harness.tools.base import Tool, ToolRegistry, ToolResult


class SequencedLLM(LLMClient):
    def __init__(self, items: list[LLMResponse | Exception]) -> None:
        self._items = list(items)
        self.messages_seen: list[list[dict[str, Any]]] = []

    def chat(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> LLMResponse:
        self.messages_seen.append(list(messages))
        if not self._items:
            raise StopIteration
        item = self._items.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class SequencedRunTestsTool(Tool):
    def __init__(self, tmp_path: Path, reports: list[dict[str, Any]]) -> None:
        self._tmp_path = tmp_path
        self._reports = list(reports)
        self.calls = 0

    @property
    def name(self) -> str:
        return "run_tests"

    @property
    def schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}, "required": []}

    def execute(self, args: dict[str, Any]) -> ToolResult:
        report = self._reports.pop(0)
        report_path = self._tmp_path / f"report-{self.calls}.json"
        report_path.write_text(json.dumps(report), encoding="utf-8")
        self.calls += 1
        return ToolResult(success=True, output={"report_path": str(report_path)})


class PendingCommandTool(Tool):
    @property
    def name(self) -> str:
        return "run_command"

    @property
    def schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {"cmd": {"type": "string"}}}

    def execute(self, args: dict[str, Any]) -> ToolResult:
        return ToolResult(
            success=False,
            output={"status": "PENDING"},
            error="command requires approval",
        )


class ApprovedCommandTool(Tool):
    def __init__(self) -> None:
        self.execute_calls = 0
        self.approved_calls = 0

    @property
    def name(self) -> str:
        return "run_command"

    @property
    def schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {"cmd": {"type": "string"}}}

    def execute(self, args: dict[str, Any]) -> ToolResult:
        self.execute_calls += 1
        return ToolResult(
            success=False,
            output={"status": "PENDING"},
            error="command requires approval",
        )

    def execute_approved(self, args: dict[str, Any]) -> ToolResult:
        self.approved_calls += 1
        return ToolResult(success=True, output={"stdout": "approved\n"})


class WriteFileToolDouble(Tool):
    def __init__(self, *, success: bool) -> None:
        self._success = success

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {"path": {"type": "string"}}}

    def execute(self, args: dict[str, Any]) -> ToolResult:
        return ToolResult(success=self._success, output={}, error="write failed")


class ScriptedApprovalBroker:
    def __init__(self, status: HITLStatus) -> None:
        self.status = status
        self.requests: list[ActionRequest] = []

    def request(self, action: Any, timeout: int) -> HITLRequest:
        self.requests.append(ActionRequest(action=action, timeout=timeout))
        return HITLRequest(
            action=action,
            status=self.status,
            timestamp=datetime.now(),
            decision=self.status.value.lower(),
            request_id=f"hitl-{len(self.requests)}",
        )


@dataclass(frozen=True)
class ActionRequest:
    action: Any
    timeout: int


def _config(tmp_path: Path, *, max_rounds: int = 5, stuck_threshold: int = 3) -> Config:
    return Config(
        max_rounds=max_rounds,
        target_directory=str(tmp_path),
        memory_file=str(tmp_path / ".harness" / "memory.json"),
        stuck_threshold=stuck_threshold,
        llm_retry_count=2,
    )


def _registry(config: Config, tool: Tool) -> ToolRegistry:
    registry = ToolRegistry(config)
    registry.register(tool)
    return registry


def _tool_call(name: str, arguments: dict[str, Any] | None = None) -> ToolCall:
    return ToolCall(id=f"call-{name}", name=name, arguments=arguments or {})


def _response(name: str, arguments: dict[str, Any] | None = None) -> LLMResponse:
    return LLMResponse(
        content="",
        finish_reason="tool_calls",
        tool_calls=[_tool_call(name, arguments)],
    )


def _multi_response(calls: list[ToolCall]) -> LLMResponse:
    return LLMResponse(content="", finish_reason="tool_calls", tool_calls=calls)


def _no_tool_response(content: str = "I cannot help") -> LLMResponse:
    return LLMResponse(content=content, finish_reason="stop", tool_calls=[])


def _pytest_report(
    exitcode: int,
    message: str = "AssertionError: assert 1 == 2",
) -> dict[str, Any]:
    if exitcode == 0:
        return {
            "exitcode": 0,
            "summary": {"passed": 1, "failed": 0},
            "tests": [{"nodeid": "tests/test_sample.py::test_example", "outcome": "passed"}],
        }
    return {
        "exitcode": exitcode,
        "summary": {"passed": 0, "failed": 1},
        "tests": [
            {
                "nodeid": "tests/test_sample.py::test_example",
                "outcome": "failed",
                "call": {
                    "crash": {
                        "message": message,
                        "path": "tests/test_sample.py",
                        "lineno": 12,
                    },
                    "longrepr": message,
                },
            }
        ],
    }


def test_run_feeds_back_failing_tests_until_pass(tmp_path: Path) -> None:
    config = _config(tmp_path)
    llm = SequencedLLM([_response("run_tests"), _response("run_tests")])
    run_tests = SequencedRunTestsTool(
        tmp_path,
        [_pytest_report(1), _pytest_report(0)],
    )
    loop = AgentLoop(config, llm, _registry(config, run_tests))

    result = loop.run("make the test pass")

    assert result.status == StopReason.PASS
    assert [record.outcome.value for record in result.rounds] == ["FAIL", "PASS"]
    assert run_tests.calls == 2
    second_prompt = "\n".join(str(message) for message in llm.messages_seen[1])
    assert "failure_type: ASSERTION" in second_prompt
    assert "Inspect the failing assertion" in second_prompt


def test_run_stops_at_max_rounds(tmp_path: Path) -> None:
    config = _config(tmp_path, max_rounds=2, stuck_threshold=99)
    llm = SequencedLLM([_response("run_tests"), _response("run_tests")])
    run_tests = SequencedRunTestsTool(
        tmp_path,
        [
            _pytest_report(1, "AssertionError: assert 1 == 2"),
            _pytest_report(1, "AssertionError: assert 2 == 3"),
        ],
    )
    loop = AgentLoop(config, llm, _registry(config, run_tests))

    result = loop.run("try twice")

    assert result.status == StopReason.MAX_ROUNDS
    assert len(result.rounds) == 2


def test_run_stops_when_same_failure_is_stuck(tmp_path: Path) -> None:
    config = _config(tmp_path, max_rounds=5, stuck_threshold=2)
    llm = SequencedLLM([_response("run_tests"), _response("run_tests")])
    run_tests = SequencedRunTestsTool(
        tmp_path,
        [_pytest_report(1), _pytest_report(1)],
    )
    loop = AgentLoop(config, llm, _registry(config, run_tests))

    result = loop.run("avoid looping")

    assert result.status == StopReason.STUCK
    assert len(result.rounds) == 2


def test_run_stops_when_governance_requires_approval_and_hitl_is_pending(
    tmp_path: Path,
) -> None:
    config = _config(tmp_path)
    registry = ToolRegistry(config)
    registry.register(PendingCommandTool())
    llm = SequencedLLM([_response("run_command", {"cmd": "rm -rf .cache"})])
    loop = AgentLoop(config, llm, registry)

    result = loop.run("run a dangerous command")

    assert result.status == StopReason.HITL_DENIED
    assert result.rounds[0].actions[0].tool_name == "run_command"
    assert result.rounds[0].outcome.value == "HITL_DENIED"
    assert result.rounds[0].strategy_used == "hitl_pending"


def test_run_publishes_lifecycle_events_for_passing_test_round(tmp_path: Path) -> None:
    config = _config(tmp_path)
    llm = SequencedLLM([_response("run_tests")])
    run_tests = SequencedRunTestsTool(tmp_path, [_pytest_report(0)])
    events: list[Any] = []

    loop = AgentLoop(
        config,
        llm,
        _registry(config, run_tests),
        event_sink=events.append,
    )

    result = loop.run("show progress")

    assert result.status == StopReason.PASS
    assert [event.event_type for event in events] == [
        RunEventType.TASK_STARTED,
        RunEventType.ROUND_STARTED,
        RunEventType.MODEL_RESPONSE,
        RunEventType.TOOL_REQUESTED,
        RunEventType.TESTS_STARTED,
        RunEventType.TESTS_COMPLETED,
        RunEventType.RUN_FINISHED,
    ]
    assert events[-1].stop_reason == "PASS"


def test_run_executes_approved_command_once_then_continues(tmp_path: Path) -> None:
    config = _config(tmp_path)
    llm = SequencedLLM(
        [
            _multi_response(
                [
                    _tool_call("run_command", {"cmd": "rm -rf build"}),
                    _tool_call("run_tests"),
                ]
            )
        ]
    )
    command = ApprovedCommandTool()
    run_tests = SequencedRunTestsTool(tmp_path, [_pytest_report(0)])
    registry = ToolRegistry(config)
    registry.register(command)
    registry.register(run_tests)
    broker = ScriptedApprovalBroker(HITLStatus.APPROVED)

    loop = AgentLoop(config, llm, registry, approval_broker=broker)

    result = loop.run("approve then test")

    assert result.status == StopReason.PASS
    assert command.execute_calls == 1
    assert command.approved_calls == 1
    assert broker.requests[0].action.tool_name == "run_command"
    assert result.rounds[0].outcome.value == "PASS"


def test_run_denied_hitl_feedback_continues_to_next_round(tmp_path: Path) -> None:
    config = _config(tmp_path)
    llm = SequencedLLM([_response("run_command"), _response("run_tests")])
    command = ApprovedCommandTool()
    run_tests = SequencedRunTestsTool(tmp_path, [_pytest_report(0)])
    registry = ToolRegistry(config)
    registry.register(command)
    registry.register(run_tests)
    broker = ScriptedApprovalBroker(HITLStatus.DENIED)

    loop = AgentLoop(config, llm, registry, approval_broker=broker)

    result = loop.run("deny then recover")

    assert result.status == StopReason.PASS
    assert command.approved_calls == 0
    assert result.rounds[0].outcome.value == "FAIL"
    assert result.rounds[0].strategy_used == "hitl_denied"
    second_prompt = "\n".join(str(message) for message in llm.messages_seen[1])
    assert "hitl_denied" in second_prompt


def test_run_retries_llm_failures_before_dispatching_tool(tmp_path: Path) -> None:
    config = _config(tmp_path)
    llm = SequencedLLM([RuntimeError("temporary llm failure"), _response("run_tests")])
    run_tests = SequencedRunTestsTool(tmp_path, [_pytest_report(0)])
    loop = AgentLoop(config, llm, _registry(config, run_tests))

    result = loop.run("retry once")

    assert result.status == StopReason.PASS
    assert len(llm.messages_seen) == 2
    assert run_tests.calls == 1


def test_run_does_not_treat_missing_tool_calls_as_pass(tmp_path: Path) -> None:
    config = _config(tmp_path, max_rounds=1)
    llm = SequencedLLM([_no_tool_response()])
    registry = ToolRegistry(config)
    loop = AgentLoop(config, llm, registry)

    result = loop.run("do the work")

    assert result.status == StopReason.MAX_ROUNDS
    assert result.rounds[0].outcome.value == "FAIL"


def test_tool_dispatch_failure_is_fed_back_to_next_round(tmp_path: Path) -> None:
    config = _config(tmp_path)
    llm = SequencedLLM([_response("missing_tool"), _response("run_tests")])
    run_tests = SequencedRunTestsTool(tmp_path, [_pytest_report(0)])
    registry = _registry(config, run_tests)
    loop = AgentLoop(config, llm, registry)

    result = loop.run("use an unknown tool then recover")

    assert result.status == StopReason.PASS
    second_prompt = "\n".join(str(message) for message in llm.messages_seen[1])
    assert "missing_tool" in second_prompt
    assert "tool_error" in second_prompt


def test_output_files_include_only_successful_writes(tmp_path: Path) -> None:
    config = _config(tmp_path, max_rounds=1)
    llm = SequencedLLM([_response("write_file", {"path": "created.py"})])
    loop = AgentLoop(config, llm, _registry(config, WriteFileToolDouble(success=False)))

    result = loop.run("write a file")

    assert result.output_files == []
