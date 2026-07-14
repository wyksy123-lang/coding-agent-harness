from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from harness.agent_loop import AgentLoop
from harness.governance.hitl import HITLState
from harness.llm.base import ToolCall
from harness.llm.mock import MockLLMClient
from harness.memory.retriever import MemoryRetriever
from harness.models import Config, FailureType, HITLRequest, HITLStatus, StopReason
from harness.tools.base import Tool, ToolRegistry, ToolResult
from harness.tools.shell import RunCommandTool


class RecordingWriteFileTool(Tool):
    def __init__(self) -> None:
        self.writes: list[dict[str, str]] = []

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        }

    def execute(self, args: dict[str, Any]) -> ToolResult:
        path = str(args.get("path", ""))
        content = str(args.get("content", ""))
        self.writes.append({"path": path, "content": content})
        return ToolResult(success=True, output={"path": path})


class SequencedRunTestsTool(Tool):
    def __init__(self, reports: list[dict[str, Any]]) -> None:
        self._reports = list(reports)
        self.calls = 0

    @property
    def name(self) -> str:
        return "run_tests"

    @property
    def schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}, "required": []}

    def execute(self, args: dict[str, Any]) -> ToolResult:
        self.calls += 1
        return ToolResult(
            success=True,
            output={"report_json": json.dumps(self._reports.pop(0))},
        )


class FinishTool(Tool):
    @property
    def name(self) -> str:
        return "finish"

    @property
    def schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"reason": {"type": "string"}},
            "required": ["reason"],
        }

    def execute(self, args: dict[str, Any]) -> ToolResult:
        return ToolResult(success=True, output={})


class RecordingHITLState(HITLState):
    def __init__(self) -> None:
        super().__init__()
        self.created: list[HITLRequest] = []

    def create(self, action: Any, timeout: int) -> HITLRequest:
        request = super().create(action, timeout)
        self.created.append(request)
        return request


def _config(tmp_path: Path, *, max_rounds: int = 8, stuck_threshold: int = 3) -> Config:
    return Config(
        max_rounds=max_rounds,
        target_directory=str(tmp_path),
        memory_file=str(tmp_path / ".harness" / "memory.json"),
        stuck_threshold=stuck_threshold,
        llm_retry_count=0,
    )


def _registry(config: Config, *tools: Tool) -> ToolRegistry:
    registry = ToolRegistry(config)
    for tool in tools:
        registry.register(tool)
    return registry


def _tool_call(
    name: str,
    arguments: dict[str, Any] | None = None,
    *,
    call_id: str | None = None,
) -> ToolCall:
    return ToolCall(id=call_id or f"call-{name}", name=name, arguments=arguments or {})


def _pytest_report(exitcode: int, message: str = "AssertionError: assert 1 == 2") -> dict[str, Any]:
    if exitcode == 0:
        return {
            "exitcode": 0,
            "summary": {"passed": 1, "failed": 0},
            "tests": [
                {
                    "nodeid": "tests/test_feature.py::test_feature",
                    "outcome": "passed",
                }
            ],
        }
    return {
        "exitcode": exitcode,
        "summary": {"passed": 0, "failed": 1},
        "tests": [
            {
                "nodeid": "tests/test_feature.py::test_feature",
                "outcome": "failed",
                "call": {
                    "crash": {
                        "message": message,
                        "path": "tests/test_feature.py",
                        "lineno": 4,
                    },
                    "longrepr": message,
                },
            }
        ],
    }


def _all_message_text(mock_llm: MockLLMClient, call_index: int) -> str:
    return "\n".join(
        str(message.get("content", ""))
        for message in mock_llm.recorded_calls[call_index].messages
    )


def test_mock_llm_drives_full_tdd_loop_and_records_memory(tmp_path: Path) -> None:
    config = _config(tmp_path)
    write_file = RecordingWriteFileTool()
    run_tests = SequencedRunTestsTool([_pytest_report(1), _pytest_report(0)])
    llm = MockLLMClient.from_tool_calls(
        [
            [
                _tool_call(
                    "write_file",
                    {
                        "path": "tests/test_feature.py",
                        "content": "from app import add\n\n"
                        "def test_feature():\n    assert add(1, 2) == 3\n",
                    },
                    call_id="write-red-test",
                )
            ],
            [_tool_call("run_tests", call_id="run-red")],
            [
                _tool_call(
                    "write_file",
                    {
                        "path": "app.py",
                        "content": "def add(left: int, right: int) -> int:\n"
                        "    return left + right\n",
                    },
                    call_id="write-green-code",
                )
            ],
            [
                _tool_call("run_tests", call_id="run-green"),
                _tool_call("finish", {"reason": "tests pass"}, call_id="finish"),
            ],
        ]
    )
    loop = AgentLoop(
        config,
        llm,
        _registry(config, write_file, run_tests, FinishTool()),
    )

    result = loop.run("implement add with TDD")

    assert result.status == StopReason.PASS
    assert [record.outcome.value for record in result.rounds] == [
        "FAIL",
        "FAIL",
        "FAIL",
        "PASS",
    ]
    assert result.rounds[-1].actions[-1].tool_name == "finish"
    assert run_tests.calls == 2
    assert [write["path"] for write in write_file.writes] == [
        "tests/test_feature.py",
        "app.py",
    ]
    feedback_prompt = _all_message_text(llm, 2)
    assert "failure_type: ASSERTION" in feedback_prompt
    assert "Inspect the failing assertion" in feedback_prompt
    assert "relevant_memory" in feedback_prompt

    memory = MemoryRetriever(config.memory_file)
    assertion_entries = memory.retrieve_relevant(FailureType.ASSERTION)
    assert len(assertion_entries) == 1
    assert assertion_entries[0].test_name == "tests/test_feature.py::test_feature"
    assert assertion_entries[0].outcome == "unresolved"


def test_mock_llm_cannot_finish_before_green_tests(tmp_path: Path) -> None:
    config = _config(tmp_path, max_rounds=1)
    llm = MockLLMClient.from_tool_calls(
        [[_tool_call("finish", {"reason": "done without tests"})]]
    )
    loop = AgentLoop(config, llm, _registry(config, FinishTool()))

    result = loop.run("do not skip red green")

    assert result.status == StopReason.MAX_ROUNDS
    assert result.rounds[0].outcome.value == "FAIL"
    assert result.rounds[0].strategy_used == "finish_before_green"


def test_mock_llm_feedback_changes_next_action(tmp_path: Path) -> None:
    config = _config(tmp_path)
    write_file = RecordingWriteFileTool()
    run_tests = SequencedRunTestsTool([_pytest_report(1), _pytest_report(0)])
    llm = MockLLMClient.from_tool_calls(
        [
            [_tool_call("run_tests", call_id="first-red")],
            [
                _tool_call(
                    "write_file",
                    {"path": "app.py", "content": "def fixed() -> bool:\n    return True\n"},
                    call_id="write-fix-after-feedback",
                )
            ],
            [_tool_call("run_tests", call_id="green-after-fix")],
        ]
    )
    loop = AgentLoop(config, llm, _registry(config, write_file, run_tests))

    result = loop.run("use feedback to fix the failure")

    assert result.status == StopReason.PASS
    second_call_prompt = _all_message_text(llm, 1)
    assert "failure_type: ASSERTION" in second_call_prompt
    assert write_file.writes == [
        {"path": "app.py", "content": "def fixed() -> bool:\n    return True\n"}
    ]


def test_mock_llm_dangerous_command_is_intercepted_by_hitl(tmp_path: Path) -> None:
    config = _config(tmp_path)
    run_tests = SequencedRunTestsTool([_pytest_report(0)])
    hitl_state = RecordingHITLState()
    llm = MockLLMClient.from_tool_calls(
        [
            [_tool_call("run_command", {"cmd": "rm -rf .harness"}, call_id="danger")],
            [_tool_call("run_tests", call_id="recover")],
        ]
    )
    loop = AgentLoop(
        config,
        llm,
        _registry(
            config,
            RunCommandTool(
                config.target_directory,
                config.dangerous_command_patterns,
                timeout=1,
            ),
            run_tests,
        ),
        hitl_state=hitl_state,
    )

    result = loop.run("request a dangerous command")

    assert result.status == StopReason.PASS
    assert result.rounds[0].outcome.value == "HITL_DENIED"
    assert result.rounds[0].actions[0].args["cmd"] == "rm -rf .harness"
    assert hitl_state.created
    assert hitl_state.created[0].status == HITLStatus.DENIED
    assert "denied" in _all_message_text(llm, 1)


def test_mock_llm_stopping_reasons_are_deterministic(tmp_path: Path) -> None:
    pass_config = _config(tmp_path / "pass")
    pass_tests = SequencedRunTestsTool([_pytest_report(0)])
    pass_loop = AgentLoop(
        pass_config,
        MockLLMClient.from_tool_calls([[_tool_call("run_tests")]]),
        _registry(pass_config, pass_tests),
    )
    assert pass_loop.run("green immediately").status == StopReason.PASS

    max_config = _config(tmp_path / "max", max_rounds=2, stuck_threshold=99)
    max_tests = SequencedRunTestsTool(
        [
            _pytest_report(1, "AssertionError: assert 1 == 2"),
            _pytest_report(1, "AssertionError: assert 2 == 3"),
        ]
    )
    max_loop = AgentLoop(
        max_config,
        MockLLMClient.from_tool_calls(
            [[_tool_call("run_tests")], [_tool_call("run_tests")]]
        ),
        _registry(max_config, max_tests),
    )
    assert max_loop.run("stop at max rounds").status == StopReason.MAX_ROUNDS

    stuck_config = _config(tmp_path / "stuck", max_rounds=5, stuck_threshold=2)
    stuck_tests = SequencedRunTestsTool(
        [
            _pytest_report(1, "AssertionError: assert 1 == 2"),
            _pytest_report(1, "AssertionError: assert 1 == 2"),
        ]
    )
    stuck_loop = AgentLoop(
        stuck_config,
        MockLLMClient.from_tool_calls(
            [[_tool_call("run_tests")], [_tool_call("run_tests")]]
        ),
        _registry(stuck_config, stuck_tests),
    )
    assert stuck_loop.run("detect stuck loop").status == StopReason.STUCK
