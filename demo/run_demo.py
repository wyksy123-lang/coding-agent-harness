from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from harness.agent_loop import AgentLoop
from harness.governance.hitl import HITLState
from harness.llm.base import LLMClient, LLMResponse, ToolCall
from harness.llm.mock import MockLLMClient
from harness.models import Config, HITLRequest, StopReason
from harness.tools.base import Tool, ToolRegistry, ToolResult
from harness.tools.shell import RunCommandTool


@dataclass(frozen=True)
class DemoResult:
    name: str
    stop_reason: StopReason
    evidence: dict[str, Any]


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

    @property
    def name(self) -> str:
        return "run_tests"

    @property
    def schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}, "required": []}

    def execute(self, args: dict[str, Any]) -> ToolResult:
        del args
        if not self._reports:
            return ToolResult(success=False, output={}, error="no test report queued")
        return ToolResult(
            success=True,
            output={"report_json": json.dumps(self._reports.pop(0))},
        )


class RecordingHITLState(HITLState):
    def __init__(self) -> None:
        super().__init__()
        self.created: list[HITLRequest] = []

    def create(self, action: Any, timeout: int) -> HITLRequest:
        request = super().create(action, timeout)
        self.created.append(request)
        return request


class FeedbackDrivenLLM(LLMClient):
    def __init__(self) -> None:
        self.feedback_seen = False
        self.recorded_calls: list[list[dict[str, Any]]] = []

    def chat(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> LLMResponse:
        del tools
        self.recorded_calls.append(list(messages))
        if len(self.recorded_calls) == 1:
            return _response([_tool_call("run_tests", call_id="red-tests")])

        prompt = "\n".join(str(message.get("content", "")) for message in messages)
        self.feedback_seen = "failure_type: ASSERTION" in prompt
        if self.feedback_seen and len(self.recorded_calls) == 2:
            return _response(
                [
                    _tool_call(
                        "write_file",
                        {
                            "path": "app.py",
                            "content": "def fixed() -> bool:\n    return True\n",
                        },
                        call_id="write-fix",
                    )
                ]
            )
        return _response([_tool_call("run_tests", call_id="green-tests")])


def demonstrate_governance_interception(base_dir: str | Path | None = None) -> DemoResult:
    if base_dir is None:
        with tempfile.TemporaryDirectory(prefix="coding-agent-harness-demo-") as tmp_dir:
            return demonstrate_governance_interception(tmp_dir)

    workspace = _workspace(base_dir, "governance")
    config = _config(workspace)
    command = "rm -rf .harness"
    hitl_state = RecordingHITLState()
    llm = MockLLMClient.from_tool_calls(
        [[_tool_call("run_command", {"cmd": command}, call_id="danger")]]
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
        ),
        hitl_state=hitl_state,
    )

    result = loop.run("demonstrate governance interception")
    request = hitl_state.created[0]
    return DemoResult(
        name="governance_interception",
        stop_reason=result.status,
        evidence={
            "intercepted": bool(hitl_state.created),
            "command": command,
            "hitl_status": request.status.value,
            "first_round_outcome": result.rounds[0].outcome.value,
        },
    )


def demonstrate_feedback_correction(base_dir: str | Path | None = None) -> DemoResult:
    if base_dir is None:
        with tempfile.TemporaryDirectory(prefix="coding-agent-harness-demo-") as tmp_dir:
            return demonstrate_feedback_correction(tmp_dir)

    workspace = _workspace(base_dir, "feedback")
    config = _config(workspace)
    llm = FeedbackDrivenLLM()
    run_tests = SequencedRunTestsTool([_pytest_report(1), _pytest_report(0)])
    write_file = RecordingWriteFileTool()
    loop = AgentLoop(config, llm, _registry(config, run_tests, write_file))

    result = loop.run("demonstrate feedback correction")
    actions_by_round = [
        [action.tool_name for action in round_record.actions]
        for round_record in result.rounds
    ]
    return DemoResult(
        name="feedback_correction",
        stop_reason=result.status,
        evidence={
            "feedback_seen": llm.feedback_seen,
            "changed_action": actions_by_round[0] != actions_by_round[1],
            "actions_by_round": actions_by_round,
            "writes": list(write_file.writes),
        },
    )


def demonstrate_stuck_detection(base_dir: str | Path | None = None) -> DemoResult:
    if base_dir is None:
        with tempfile.TemporaryDirectory(prefix="coding-agent-harness-demo-") as tmp_dir:
            return demonstrate_stuck_detection(tmp_dir)

    workspace = _workspace(base_dir, "stuck")
    config = _config(workspace, max_rounds=5, stuck_threshold=2)
    run_tests = SequencedRunTestsTool(
        [
            _pytest_report(1, "AssertionError: assert 1 == 2"),
            _pytest_report(1, "AssertionError: assert 1 == 2"),
        ]
    )
    loop = AgentLoop(
        config,
        MockLLMClient.from_tool_calls(
            [[_tool_call("run_tests")], [_tool_call("run_tests")]]
        ),
        _registry(config, run_tests),
    )

    result = loop.run("demonstrate stuck detection")
    fingerprints = [record.failure_fingerprint for record in result.rounds]
    return DemoResult(
        name="stuck_detection",
        stop_reason=result.status,
        evidence={
            "stuck_threshold": config.stuck_threshold,
            "round_count": len(result.rounds),
            "same_failure_fingerprint": len(set(fingerprints)) == 1,
        },
    )


def run_all_demonstrations(base_dir: str | Path | None = None) -> list[DemoResult]:
    if base_dir is None:
        with tempfile.TemporaryDirectory(prefix="coding-agent-harness-demo-") as tmp_dir:
            return run_all_demonstrations(tmp_dir)

    root = _workspace(base_dir, "mechanism-demo")
    return [
        demonstrate_governance_interception(root),
        demonstrate_feedback_correction(root),
        demonstrate_stuck_detection(root),
    ]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="coding-agent-harness-demo-") as tmp_dir:
        results = run_all_demonstrations(tmp_dir)
    for result in results:
        print(f"{result.name}: {result.stop_reason.value}")
    expected = {
        "governance_interception": StopReason.HITL_DENIED,
        "feedback_correction": StopReason.PASS,
        "stuck_detection": StopReason.STUCK,
    }
    return 0 if all(result.stop_reason == expected[result.name] for result in results) else 1


def _config(
    target_directory: Path,
    *,
    max_rounds: int = 6,
    stuck_threshold: int = 3,
) -> Config:
    return Config(
        max_rounds=max_rounds,
        target_directory=str(target_directory),
        memory_file=str(target_directory / ".harness" / "memory.json"),
        stuck_threshold=stuck_threshold,
        llm_retry_count=0,
    )


def _registry(config: Config, *tools: Tool) -> ToolRegistry:
    registry = ToolRegistry(config)
    for tool in tools:
        registry.register(tool)
    return registry


def _workspace(base_dir: str | Path | None, name: str) -> Path:
    root = Path(base_dir) if base_dir is not None else Path.cwd()
    workspace = root / name
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


def _tool_call(
    name: str,
    arguments: dict[str, Any] | None = None,
    *,
    call_id: str | None = None,
) -> ToolCall:
    return ToolCall(id=call_id or f"call-{name}", name=name, arguments=arguments or {})


def _response(tool_calls: list[ToolCall]) -> LLMResponse:
    return LLMResponse(content="", finish_reason="tool_calls", tool_calls=tool_calls)


def _pytest_report(
    exitcode: int,
    message: str = "AssertionError: assert 1 == 2",
) -> dict[str, Any]:
    if exitcode == 0:
        return {
            "exitcode": 0,
            "summary": {"passed": 1, "failed": 0},
            "tests": [{"nodeid": "tests/test_demo.py::test_demo", "outcome": "passed"}],
        }
    return {
        "exitcode": exitcode,
        "summary": {"passed": 0, "failed": 1},
        "tests": [
            {
                "nodeid": "tests/test_demo.py::test_demo",
                "outcome": "failed",
                "call": {
                    "crash": {
                        "message": message,
                        "path": "tests/test_demo.py",
                        "lineno": 4,
                    },
                    "longrepr": message,
                },
            }
        ],
    }


if __name__ == "__main__":
    raise SystemExit(main())
