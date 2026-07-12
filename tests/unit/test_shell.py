from __future__ import annotations

import os

from harness.models import Config, GuardResult
from harness.tools.base import Tool, ToolResult
from harness.tools.shell import RunCommandTool, RunTestsTool

WORKING_TEST_COMMAND = (
    "python3 -m pytest --json-report --json-report-file=.harness/report.json"
)


def _shell_config(**kwargs: object) -> Config:
    """Create a Config with a test_command that works with the installed plugin."""
    defaults: dict[str, object] = {"test_command": WORKING_TEST_COMMAND}
    defaults.update(kwargs)
    return Config(**defaults)  # type: ignore[arg-type]


def _write_passing_test(target_directory: str) -> str:
    """Write a simple passing test file into *target_directory*."""
    path = os.path.join(target_directory, "test_pass.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write("def test_pass():\n    assert True\n")
    return path


def _write_failing_test(target_directory: str) -> str:
    """Write a simple failing test file into *target_directory*."""
    path = os.path.join(target_directory, "test_fail.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write("def test_fail():\n    assert 1 == 2\n")
    return path


def _write_slow_test(target_directory: str, seconds: int = 30) -> str:
    """Write a test that sleeps for *seconds* (used for timeout tests)."""
    path = os.path.join(target_directory, "test_slow.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write(
            f"import time\n"
            f"def test_slow():\n"
            f"    time.sleep({seconds})\n"
            f"    assert True\n"
        )
    return path


def _write_syntax_error_test(target_directory: str) -> str:
    """Write a test file with a syntax error (collection error)."""
    path = os.path.join(target_directory, "test_syntax.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write("def test_broken(\n")
    return path


# ---------------------------------------------------------------------------
# RunCommandTool — construction
# ---------------------------------------------------------------------------


class TestRunCommandToolConstruction:
    """Verify RunCommandTool can be constructed and has the Tool API surface."""

    def test_can_construct_with_target_directory_and_patterns(self, tmp_workspace):
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=[],
        )
        assert isinstance(tool, RunCommandTool)

    def test_is_subclass_of_tool(self, tmp_workspace):
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=[],
        )
        assert isinstance(tool, Tool)

    def test_name_returns_run_command(self, tmp_workspace):
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=[],
        )
        assert tool.name == "run_command"

    def test_schema_returns_dict(self, tmp_workspace):
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=[],
        )
        assert isinstance(tool.schema, dict)

    def test_schema_has_type_object(self, tmp_workspace):
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=[],
        )
        assert tool.schema["type"] == "object"

    def test_schema_has_properties(self, tmp_workspace):
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=[],
        )
        assert "properties" in tool.schema

    def test_schema_declares_cmd_property(self, tmp_workspace):
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=[],
        )
        assert "cmd" in tool.schema["properties"]

    def test_schema_lists_cmd_required(self, tmp_workspace):
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=[],
        )
        assert "cmd" in tool.schema.get("required", [])


# ---------------------------------------------------------------------------
# RunCommandTool — safe command execution
# ---------------------------------------------------------------------------


class TestRunCommandToolSafeExecution:
    """SPEC §3.2.5: safe commands execute and return stdout/stderr/exit_code."""

    def test_echo_hello_returns_success(self, tmp_workspace):
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=[],
        )
        result = tool.execute({"cmd": "echo hello"})
        assert isinstance(result, ToolResult)
        assert result.success is True

    def test_echo_hello_stdout_contains_text(self, tmp_workspace):
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=[],
        )
        result = tool.execute({"cmd": "echo hello"})
        assert "hello" in result.output["stdout"]

    def test_echo_hello_exit_code_zero(self, tmp_workspace):
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=[],
        )
        result = tool.execute({"cmd": "echo hello"})
        assert result.output["exit_code"] == 0

    def test_command_with_stderr_captured(self, tmp_workspace):
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=[],
        )
        result = tool.execute({"cmd": "echo error >&2"})
        assert result.success is True
        assert "error" in result.output["stderr"]
        assert result.output["stdout"] == ""

    def test_command_with_both_stdout_and_stderr(self, tmp_workspace):
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=[],
        )
        result = tool.execute({"cmd": "echo out && echo err >&2"})
        assert result.success is True
        assert "out" in result.output["stdout"]
        assert "err" in result.output["stderr"]

    def test_command_with_arguments_executes(self, tmp_workspace):
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=[],
        )
        result = tool.execute({"cmd": "echo hello world"})
        assert result.success is True
        assert "hello world" in result.output["stdout"]
        assert result.output["exit_code"] == 0

    def test_output_dict_has_stdout_key(self, tmp_workspace):
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=[],
        )
        result = tool.execute({"cmd": "echo hi"})
        assert "stdout" in result.output

    def test_output_dict_has_stderr_and_exit_code_keys(self, tmp_workspace):
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=[],
        )
        result = tool.execute({"cmd": "echo hi"})
        assert "stderr" in result.output
        assert "exit_code" in result.output

    def test_command_runs_in_target_directory(self, tmp_workspace):
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=[],
        )
        result = tool.execute({"cmd": "pwd"})
        assert result.success is True
        assert os.path.realpath(tmp_workspace) in os.path.realpath(
            result.output["stdout"].strip()
        )


# ---------------------------------------------------------------------------
# RunCommandTool — failed command execution
# ---------------------------------------------------------------------------


class TestRunCommandToolFailedExecution:
    """SPEC §3.2.5: command failure returns exit_code != 0; tool still succeeds."""

    def test_false_command_returns_nonzero_exit_code(self, tmp_workspace):
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=[],
        )
        result = tool.execute({"cmd": "false"})
        assert result.output["exit_code"] != 0

    def test_exit_1_command_returns_exit_code_1(self, tmp_workspace):
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=[],
        )
        result = tool.execute({"cmd": "exit 1"})
        assert result.output["exit_code"] == 1

    def test_failed_command_success_still_true(self, tmp_workspace):
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=[],
        )
        result = tool.execute({"cmd": "false"})
        assert result.success is True


# ---------------------------------------------------------------------------
# RunCommandTool — dangerous command blocking (CommandGuard integration)
# ---------------------------------------------------------------------------


class TestRunCommandToolDangerousCommands:
    """SPEC §3.2.5: dangerous commands → PENDING (not executed)."""

    def test_rm_rf_returns_pending(self, tmp_workspace, mock_config):
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=mock_config.dangerous_command_patterns,
        )
        result = tool.execute({"cmd": "rm -rf /tmp/test"})
        assert result.success is False
        assert result.output.get("status") == GuardResult.PENDING.value

    def test_git_push_returns_pending(self, tmp_workspace, mock_config):
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=mock_config.dangerous_command_patterns,
        )
        result = tool.execute({"cmd": "git push origin main"})
        assert result.success is False
        assert result.output.get("status") == GuardResult.PENDING.value

    def test_sudo_returns_pending(self, tmp_workspace, mock_config):
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=mock_config.dangerous_command_patterns,
        )
        result = tool.execute({"cmd": "sudo apt-get update"})
        assert result.success is False
        assert result.output.get("status") == GuardResult.PENDING.value

    def test_curl_returns_pending(self, tmp_workspace, mock_config):
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=mock_config.dangerous_command_patterns,
        )
        result = tool.execute({"cmd": "curl http://example.com"})
        assert result.success is False
        assert result.output.get("status") == GuardResult.PENDING.value

    def test_docker_returns_pending(self, tmp_workspace, mock_config):
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=mock_config.dangerous_command_patterns,
        )
        result = tool.execute({"cmd": "docker run -it ubuntu bash"})
        assert result.success is False
        assert result.output.get("status") == GuardResult.PENDING.value

    def test_dangerous_command_not_executed(self, tmp_workspace, mock_config):
        """When CommandGuard returns PENDING, the command must NOT be executed."""
        marker = os.path.join(tmp_workspace, "marker.txt")
        with open(marker, "w", encoding="utf-8") as f:
            f.write("safe")
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=mock_config.dangerous_command_patterns,
        )
        result = tool.execute({"cmd": f"rm -rf {marker}"})
        assert result.success is False
        assert result.output.get("status") == GuardResult.PENDING.value
        assert os.path.exists(marker), "marker file must still exist (cmd not executed)"

    def test_dangerous_command_uses_config_patterns(self, tmp_workspace, mock_config):
        """The tool must use the dangerous_command_patterns passed to it."""
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=mock_config.dangerous_command_patterns,
        )
        result = tool.execute({"cmd": "rm -rf /tmp/test"})
        assert result.output.get("status") == GuardResult.PENDING.value

    def test_custom_patterns_block_command(self, tmp_workspace):
        """Custom patterns should block matching commands."""
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=[r"forbidden"],
        )
        result = tool.execute({"cmd": "echo forbidden"})
        assert result.success is False
        assert result.output.get("status") == GuardResult.PENDING.value

    def test_custom_patterns_allow_safe_command(self, tmp_workspace):
        """Custom patterns should allow non-matching commands."""
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=[r"forbidden"],
        )
        result = tool.execute({"cmd": "echo safe"})
        assert result.success is True
        assert "safe" in result.output["stdout"]

    def test_empty_patterns_allow_all_commands(self, tmp_workspace):
        """Empty pattern list means everything is ALLOWed."""
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=[],
        )
        result = tool.execute({"cmd": "echo allgood"})
        assert result.success is True
        assert "allgood" in result.output["stdout"]

    def test_compound_dangerous_command_pending(self, tmp_workspace, mock_config):
        """A compound command containing a dangerous part must be PENDING."""
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=mock_config.dangerous_command_patterns,
        )
        result = tool.execute({"cmd": "echo safe && rm -rf /tmp"})
        assert result.success is False
        assert result.output.get("status") == GuardResult.PENDING.value

    def test_safe_compound_command_allowed(self, tmp_workspace, mock_config):
        """A compound command with no dangerous parts must be ALLOWed."""
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=mock_config.dangerous_command_patterns,
        )
        result = tool.execute({"cmd": "echo a && echo b"})
        assert result.success is True
        assert "a" in result.output["stdout"]
        assert "b" in result.output["stdout"]


# ---------------------------------------------------------------------------
# RunCommandTool — timeout handling
# ---------------------------------------------------------------------------


class TestRunCommandToolTimeout:
    """SPEC §3.2.5: commands that exceed timeout must return a timeout error."""

    def test_timeout_returns_error(self, tmp_workspace):
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=[],
            timeout=1,
        )
        result = tool.execute({"cmd": "sleep 5"})
        assert isinstance(result, ToolResult)
        assert result.success is False
        assert result.error is not None
        assert "timeout" in result.error.lower()

    def test_timeout_with_short_timeout(self, tmp_workspace):
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=[],
            timeout=2,
        )
        result = tool.execute({"cmd": "sleep 10"})
        assert result.success is False
        assert result.error is not None


# ---------------------------------------------------------------------------
# RunCommandTool — edge cases
# ---------------------------------------------------------------------------


class TestRunCommandToolEdgeCases:
    """Edge cases: empty command, missing cmd key, None cmd."""

    def test_empty_command_handled_gracefully(self, tmp_workspace):
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=[],
        )
        result = tool.execute({"cmd": ""})
        assert isinstance(result, ToolResult)
        assert result.output["exit_code"] == 0

    def test_missing_cmd_key_handled(self, tmp_workspace):
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=[],
        )
        result = tool.execute({})
        assert isinstance(result, ToolResult)
        assert result.success is False
        assert result.error is not None

    def test_none_cmd_handled(self, tmp_workspace):
        tool = RunCommandTool(
            target_directory=tmp_workspace,
            dangerous_command_patterns=[],
        )
        result = tool.execute({"cmd": None})
        assert isinstance(result, ToolResult)
        assert result.success is False
        assert result.error is not None


# ---------------------------------------------------------------------------
# RunTestsTool — construction
# ---------------------------------------------------------------------------


class TestRunTestsToolConstruction:
    """Verify RunTestsTool can be constructed and has the Tool API surface."""

    def test_can_construct_with_target_directory_and_command(self, tmp_workspace):
        tool = RunTestsTool(
            target_directory=tmp_workspace,
            test_command=WORKING_TEST_COMMAND,
            pytest_timeout=60,
        )
        assert isinstance(tool, RunTestsTool)

    def test_is_subclass_of_tool(self, tmp_workspace):
        tool = RunTestsTool(
            target_directory=tmp_workspace,
            test_command=WORKING_TEST_COMMAND,
            pytest_timeout=60,
        )
        assert isinstance(tool, Tool)

    def test_name_returns_run_tests(self, tmp_workspace):
        tool = RunTestsTool(
            target_directory=tmp_workspace,
            test_command=WORKING_TEST_COMMAND,
            pytest_timeout=60,
        )
        assert tool.name == "run_tests"

    def test_schema_returns_dict(self, tmp_workspace):
        tool = RunTestsTool(
            target_directory=tmp_workspace,
            test_command=WORKING_TEST_COMMAND,
            pytest_timeout=60,
        )
        assert isinstance(tool.schema, dict)

    def test_schema_has_type_object(self, tmp_workspace):
        tool = RunTestsTool(
            target_directory=tmp_workspace,
            test_command=WORKING_TEST_COMMAND,
            pytest_timeout=60,
        )
        assert tool.schema["type"] == "object"

    def test_schema_has_no_required_params(self, tmp_workspace):
        """SPEC §3.2.4: run_tests takes no input — uses test_command config."""
        tool = RunTestsTool(
            target_directory=tmp_workspace,
            test_command=WORKING_TEST_COMMAND,
            pytest_timeout=60,
        )
        required = tool.schema.get("required", [])
        assert required == []


# ---------------------------------------------------------------------------
# RunTestsTool — execution
# ---------------------------------------------------------------------------


class TestRunTestsToolExecution:
    """SPEC §3.2.4: run pytest and return the report.json path."""

    def test_successful_test_run_returns_report_path(self, tmp_workspace):
        _write_passing_test(tmp_workspace)
        config = _shell_config()
        tool = RunTestsTool(
            target_directory=tmp_workspace,
            test_command=config.test_command,
            pytest_timeout=config.pytest_timeout,
        )
        result = tool.execute({})
        assert isinstance(result, ToolResult)
        assert result.success is True
        assert "report_path" in result.output

    def test_failing_test_run_returns_report_path(self, tmp_workspace):
        """Even when tests fail, the report path must be returned (parsing is T12)."""
        _write_failing_test(tmp_workspace)
        config = _shell_config()
        tool = RunTestsTool(
            target_directory=tmp_workspace,
            test_command=config.test_command,
            pytest_timeout=config.pytest_timeout,
        )
        result = tool.execute({})
        assert "report_path" in result.output
        assert os.path.exists(result.output["report_path"])

    def test_report_path_points_to_existing_file(self, tmp_workspace):
        _write_passing_test(tmp_workspace)
        config = _shell_config()
        tool = RunTestsTool(
            target_directory=tmp_workspace,
            test_command=config.test_command,
            pytest_timeout=config.pytest_timeout,
        )
        result = tool.execute({})
        assert result.success is True
        report_path = result.output["report_path"]
        assert os.path.isfile(report_path)

    def test_report_path_in_output(self, tmp_workspace):
        _write_passing_test(tmp_workspace)
        config = _shell_config()
        tool = RunTestsTool(
            target_directory=tmp_workspace,
            test_command=config.test_command,
            pytest_timeout=config.pytest_timeout,
        )
        result = tool.execute({})
        assert "report_path" in result.output
        assert isinstance(result.output["report_path"], str)

    def test_uses_config_test_command(self, tmp_workspace):
        """The tool must use the test_command from the config passed to it."""
        _write_passing_test(tmp_workspace)
        config = _shell_config()
        tool = RunTestsTool(
            target_directory=tmp_workspace,
            test_command=config.test_command,
            pytest_timeout=config.pytest_timeout,
        )
        result = tool.execute({})
        assert result.success is True
        assert os.path.exists(result.output["report_path"])

    def test_runs_in_target_directory(self, tmp_workspace):
        """SPEC §3.2.4: tests must run in target_directory."""
        _write_passing_test(tmp_workspace)
        config = _shell_config()
        tool = RunTestsTool(
            target_directory=tmp_workspace,
            test_command=config.test_command,
            pytest_timeout=config.pytest_timeout,
        )
        result = tool.execute({})
        assert result.success is True
        expected_report = os.path.join(tmp_workspace, ".harness", "report.json")
        assert os.path.exists(expected_report)

    def test_harness_directory_created(self, tmp_workspace):
        """The .harness/ directory must be created if it does not exist."""
        _write_passing_test(tmp_workspace)
        harness_dir = os.path.join(tmp_workspace, ".harness")
        assert not os.path.exists(harness_dir)
        config = _shell_config()
        tool = RunTestsTool(
            target_directory=tmp_workspace,
            test_command=config.test_command,
            pytest_timeout=config.pytest_timeout,
        )
        result = tool.execute({})
        assert result.success is True
        assert os.path.isdir(harness_dir)

    def test_no_test_files_returns_report_path(self, tmp_workspace):
        """Even with no test files, the report path must be returned."""
        config = _shell_config()
        tool = RunTestsTool(
            target_directory=tmp_workspace,
            test_command=config.test_command,
            pytest_timeout=config.pytest_timeout,
        )
        result = tool.execute({})
        assert "report_path" in result.output
        assert os.path.exists(result.output["report_path"])

    def test_collection_error_returns_report_path(self, tmp_workspace):
        """SPEC §3.2.4: pytest crash → COLLECTION error; report still created."""
        _write_syntax_error_test(tmp_workspace)
        config = _shell_config()
        tool = RunTestsTool(
            target_directory=tmp_workspace,
            test_command=config.test_command,
            pytest_timeout=config.pytest_timeout,
        )
        result = tool.execute({})
        assert "report_path" in result.output
        assert os.path.exists(result.output["report_path"])


# ---------------------------------------------------------------------------
# RunTestsTool — timeout handling
# ---------------------------------------------------------------------------


class TestRunTestsToolTimeout:
    """SPEC §3.2.4: timeout → TIMEOUT error."""

    def test_timeout_with_slow_test(self, tmp_workspace):
        _write_slow_test(tmp_workspace, seconds=30)
        config = _shell_config(pytest_timeout=2)
        tool = RunTestsTool(
            target_directory=tmp_workspace,
            test_command=config.test_command,
            pytest_timeout=config.pytest_timeout,
        )
        result = tool.execute({})
        assert isinstance(result, ToolResult)
        assert result.success is False
        assert result.error is not None
        assert "timeout" in result.error.lower()


# ---------------------------------------------------------------------------
# RunTestsTool — report.json creation verification (CQ-4.1 Major fix)
# ---------------------------------------------------------------------------


class TestRunTestsToolReportCreation:
    """SPEC §3.2.4: pytest crash → report.json may not be created."""

    def test_invalid_command_returns_error_not_created(self, tmp_workspace):
        """When test_command is invalid, report.json is not created."""
        tool = RunTestsTool(
            target_directory=tmp_workspace,
            test_command="nonexistent-command-xyz",
            pytest_timeout=30,
        )
        result = tool.execute({})
        assert isinstance(result, ToolResult)
        assert result.success is False
        assert result.error is not None
        assert "not created" in result.error.lower()

    def test_missing_report_returns_exit_code(self, tmp_workspace):
        """When report.json is missing, output should contain exit_code."""
        tool = RunTestsTool(
            target_directory=tmp_workspace,
            test_command="nonexistent-command-xyz",
            pytest_timeout=30,
        )
        result = tool.execute({})
        assert result.success is False
        assert "exit_code" in result.output

    def test_valid_run_includes_exit_code(self, tmp_workspace):
        """When tests run successfully, output should include exit_code."""
        _write_passing_test(tmp_workspace)
        config = _shell_config()
        tool = RunTestsTool(
            target_directory=tmp_workspace,
            test_command=config.test_command,
            pytest_timeout=config.pytest_timeout,
        )
        result = tool.execute({})
        assert result.success is True
        assert "exit_code" in result.output
        assert result.output["exit_code"] == 0


# ---------------------------------------------------------------------------
# RunCommandTool — OSError handling (CQ-4.2 Minor fix)
# ---------------------------------------------------------------------------


class TestRunCommandToolOSError:
    """Verify that OSError (e.g. non-existent cwd) is handled gracefully."""

    def test_nonexistent_target_directory_returns_error(self):
        """CommandGuard passes but subprocess raises FileNotFoundError."""
        tool = RunCommandTool(
            target_directory="/nonexistent/dir/xyz",
            dangerous_command_patterns=[],
            timeout=5,
        )
        result = tool.execute({"cmd": "echo hello"})
        assert isinstance(result, ToolResult)
        assert result.success is False
        assert result.error is not None

    def test_nonexistent_target_directory_returns_str_error(self):
        """Error message should be a string, not an exception."""
        tool = RunCommandTool(
            target_directory="/nonexistent/dir/xyz",
            dangerous_command_patterns=[],
            timeout=5,
        )
        result = tool.execute({"cmd": "echo hello"})
        assert isinstance(result.error, str)


# ---------------------------------------------------------------------------
# RunTestsTool — OSError handling (CQ-4.2 Minor fix)
# ---------------------------------------------------------------------------


class TestRunTestsToolOSError:
    """Verify that OSError from non-existent target_directory is handled."""

    def test_nonexistent_target_directory_returns_error(self):
        tool = RunTestsTool(
            target_directory="/nonexistent/dir/xyz",
            test_command=WORKING_TEST_COMMAND,
            pytest_timeout=30,
        )
        result = tool.execute({})
        assert isinstance(result, ToolResult)
        assert result.success is False
        assert result.error is not None
