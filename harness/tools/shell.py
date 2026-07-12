from __future__ import annotations

import os
import subprocess
from typing import Any

from harness.governance.command_guard import CommandGuard
from harness.models import GuardResult
from harness.tools.base import Tool, ToolResult


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
        try:
            proc = subprocess.run(
                cmd,
                shell=True,
                cwd=self._target_directory,
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output={},
                error="command timeout",
            )
        return ToolResult(
            success=True,
            output={
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "exit_code": proc.returncode,
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
        harness_dir = os.path.join(self._target_directory, ".harness")
        report_path = os.path.join(harness_dir, "report.json")
        try:
            os.makedirs(harness_dir, exist_ok=True)
        except OSError as e:
            return ToolResult(success=False, output={}, error=str(e))
        try:
            subprocess.run(
                self._test_command,
                shell=True,
                cwd=self._target_directory,
                capture_output=True,
                text=True,
                timeout=self._pytest_timeout,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output={},
                error="test execution timeout",
            )
        return ToolResult(
            success=True,
            output={"report_path": report_path},
        )
