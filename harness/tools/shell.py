from __future__ import annotations

import json
import os
import shlex
import subprocess
from typing import Any

from harness.governance.command_guard import CommandGuard
from harness.models import GuardResult
from harness.tools.base import Tool, ToolResult

_TIMEOUT_ERROR = "command timeout"
_TEST_TIMEOUT_ERROR = "test execution timeout"
_REPORT_NOT_CREATED = "report.json not created"
_PYTEST_JSON_ARGS = ("--json-report", "--json-report-file", "--output")


def _run_shell(
    command: str,
    cwd: str,
    timeout: int,
    timeout_error: str,
) -> subprocess.CompletedProcess[str] | ToolResult:
    """Run *command* via the shell in *cwd* with a *timeout*.

    Returns either a :class:`subprocess.CompletedProcess` on success or a
    failing :class:`ToolResult` (timeout / OS error).  This helper
    centralises ``subprocess.run`` error handling for both shell tools.
    """
    try:
        return subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return ToolResult(success=False, output={}, error=timeout_error)
    except OSError as e:
        return ToolResult(success=False, output={}, error=str(e))


def _run_argv(
    command: str | list[str],
    cwd: str,
    timeout: int,
    timeout_error: str,
) -> subprocess.CompletedProcess[str] | ToolResult:
    try:
        argv = shlex.split(command) if isinstance(command, str) else command
        return subprocess.run(
            argv,
            shell=False,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return ToolResult(success=False, output={}, error=timeout_error)
    except (OSError, ValueError) as e:
        return ToolResult(success=False, output={}, error=str(e))


def _json_report_args_unavailable(result: subprocess.CompletedProcess[str]) -> bool:
    return (
        result.returncode == 4
        and "unrecognized arguments" in result.stderr
        and "--json-report" in result.stderr
    )


def _strip_json_report_args(argv: list[str]) -> list[str]:
    stripped: list[str] = []
    skip_next = False
    for arg in argv:
        if skip_next:
            skip_next = False
            continue
        if arg == "--json-report":
            continue
        if arg in {"--json-report-file", "--output"}:
            skip_next = True
            continue
        if any(arg.startswith(f"{option}=") for option in _PYTEST_JSON_ARGS):
            continue
        stripped.append(arg)
    return stripped


def _write_fallback_report(
    report_path: str,
    result: subprocess.CompletedProcess[str],
) -> None:
    summary: dict[str, int] = {"total": 0}
    if result.returncode == 0:
        summary["passed"] = 1
    elif result.returncode == 1:
        summary["failed"] = 1
    elif result.returncode == 5:
        summary["collected"] = 0
    report = {
        "exitcode": result.returncode,
        "summary": summary,
        "tests": [],
        "collectors": [],
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f)


class RunCommandTool(Tool):
    """Tool for executing shell commands with CommandGuard protection."""

    def __init__(
        self,
        target_directory: str,
        dangerous_command_patterns: list[str],
        timeout: int = 60,
    ) -> None:
        self._target_directory = target_directory
        self._dangerous_command_patterns = dangerous_command_patterns
        self._timeout = timeout

    @property
    def name(self) -> str:
        return "run_command"

    @property
    def schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "cmd": {"type": "string"},
            },
            "required": ["cmd"],
        }

    def execute(self, args: dict[str, Any]) -> ToolResult:
        cmd = args.get("cmd")
        if cmd is None:
            return ToolResult(
                success=False,
                output={},
                error="missing required argument: cmd",
            )
        guard_result = CommandGuard.check(cmd, self._dangerous_command_patterns)
        if guard_result == GuardResult.PENDING:
            return ToolResult(
                success=False,
                output={"status": GuardResult.PENDING.value},
                error="command requires approval",
            )
        result = _run_shell(
            cmd, self._target_directory, self._timeout, _TIMEOUT_ERROR
        )
        if isinstance(result, ToolResult):
            return result
        return ToolResult(
            success=True,
            output={
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
            },
        )


class RunTestsTool(Tool):
    """Tool for running the test suite and returning the report path."""

    def __init__(
        self,
        target_directory: str,
        test_command: str,
        pytest_timeout: int = 60,
    ) -> None:
        self._target_directory = target_directory
        self._test_command = test_command
        self._pytest_timeout = pytest_timeout

    @property
    def name(self) -> str:
        return "run_tests"

    @property
    def schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def execute(self, args: dict[str, Any]) -> ToolResult:
        if not os.path.isdir(self._target_directory):
            return ToolResult(
                success=False,
                output={},
                error=f"target directory does not exist: {self._target_directory}",
            )
        harness_dir = os.path.join(self._target_directory, ".harness")
        report_path = os.path.join(harness_dir, "report.json")
        try:
            os.makedirs(harness_dir, exist_ok=True)
        except OSError as e:
            return ToolResult(success=False, output={}, error=str(e))
        result = _run_argv(
            self._test_command,
            self._target_directory,
            self._pytest_timeout,
            _TEST_TIMEOUT_ERROR,
        )
        if isinstance(result, ToolResult):
            if result.error == _TEST_TIMEOUT_ERROR:
                return result
            if os.path.isdir(self._target_directory):
                return ToolResult(
                    success=False,
                    output={"exit_code": 1},
                    error=_REPORT_NOT_CREATED,
                )
            return result
        if _json_report_args_unavailable(result):
            fallback_result = _run_argv(
                _strip_json_report_args(shlex.split(self._test_command)),
                self._target_directory,
                self._pytest_timeout,
                _TEST_TIMEOUT_ERROR,
            )
            if isinstance(fallback_result, ToolResult):
                return fallback_result
            result = fallback_result
            try:
                _write_fallback_report(report_path, result)
            except OSError as e:
                return ToolResult(
                    success=False,
                    output={"exit_code": result.returncode},
                    error=str(e),
                )
        if not os.path.isfile(report_path):
            return ToolResult(
                success=False,
                output={"exit_code": result.returncode},
                error=_REPORT_NOT_CREATED,
            )
        return ToolResult(
            success=True,
            output={
                "report_path": report_path,
                "exit_code": result.returncode,
            },
        )
