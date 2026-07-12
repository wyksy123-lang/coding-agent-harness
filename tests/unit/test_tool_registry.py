from __future__ import annotations

import inspect
from dataclasses import is_dataclass
from typing import Any

import pytest

from harness.models import Action, Config
from harness.tools.base import Tool, ToolRegistry, ToolResult

_TEST_TOOL_NAMES = ["echo", "fail_tool", "noop", "custom", "raiser"]


def _test_config(**kwargs: Any) -> Config:
    """Create a Config with all test tools enabled in the whitelist."""
    defaults: dict[str, Any] = {"enabled_tools": list(_TEST_TOOL_NAMES)}
    defaults.update(kwargs)
    return Config(**defaults)


class _EchoTool(Tool):
    @property
    def name(self) -> str:
        return "echo"

    @property
    def schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Message to echo"},
            },
            "required": ["message"],
        }

    def execute(self, args: dict[str, Any]) -> ToolResult:
        return ToolResult(
            success=True,
            output={"echo": args.get("message", "")},
        )


class _FailingTool(Tool):
    @property
    def name(self) -> str:
        return "fail_tool"

    @property
    def schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def execute(self, args: dict[str, Any]) -> ToolResult:
        return ToolResult(
            success=False,
            output={},
            error="intentional failure",
        )


class _NoOpTool(Tool):
    @property
    def name(self) -> str:
        return "noop"

    @property
    def schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def execute(self, args: dict[str, Any]) -> ToolResult:
        return ToolResult(success=True, output={})


class _CustomNameTool(Tool):
    def __init__(self, tool_name: str) -> None:
        self._tool_name = tool_name

    @property
    def name(self) -> str:
        return self._tool_name

    @property
    def schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"input": {"type": "string"}},
            "required": ["input"],
        }

    def execute(self, args: dict[str, Any]) -> ToolResult:
        return ToolResult(
            success=True,
            output={"received": args.get("input", "")},
        )


class _RaisingTool(Tool):
    """A tool whose execute() raises an unexpected exception."""

    @property
    def name(self) -> str:
        return "raiser"

    @property
    def schema(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}, "required": []}

    def execute(self, args: dict[str, Any]) -> ToolResult:
        raise RuntimeError("unexpected internal error")


class TestToolResult:
    def test_tool_result_instantiation(self):
        result = ToolResult(
            success=True,
            output={"key": "value"},
            error=None,
        )
        assert result.success is True
        assert result.output == {"key": "value"}
        assert result.error is None

    def test_tool_result_is_dataclass(self):
        assert is_dataclass(ToolResult)

    def test_tool_result_success_is_bool(self):
        result = ToolResult(success=True, output={})
        assert isinstance(result.success, bool)
        assert result.success is True

    def test_tool_result_success_false(self):
        result = ToolResult(success=False, output={})
        assert result.success is False
        assert isinstance(result.success, bool)

    def test_tool_result_output_is_dict(self):
        result = ToolResult(success=True, output={"a": 1})
        assert isinstance(result.output, dict)
        assert result.output == {"a": 1}

    def test_tool_result_output_empty_dict(self):
        result = ToolResult(success=True, output={})
        assert result.output == {}

    def test_tool_result_output_nested_dict(self):
        nested = {"level1": {"level2": [1, 2, 3], "flag": True}}
        result = ToolResult(success=True, output=nested)
        assert result.output == nested
        assert result.output["level1"]["level2"] == [1, 2, 3]

    def test_tool_result_error_defaults_to_none(self):
        result = ToolResult(success=True, output={"x": 1})
        assert result.error is None

    def test_tool_result_error_can_be_string(self):
        result = ToolResult(
            success=False,
            output={},
            error="something went wrong",
        )
        assert result.error == "something went wrong"
        assert isinstance(result.error, str)

    def test_tool_result_error_can_be_none_explicit(self):
        result = ToolResult(success=True, output={}, error=None)
        assert result.error is None

    def test_tool_result_with_error_message(self):
        result = ToolResult(
            success=False,
            output={"partial": "data"},
            error="FileNotFoundError: test.py",
        )
        assert result.success is False
        assert result.output == {"partial": "data"}
        assert result.error == "FileNotFoundError: test.py"

    def test_tool_result_equality(self):
        r1 = ToolResult(success=True, output={"a": 1}, error=None)
        r2 = ToolResult(success=True, output={"a": 1}, error=None)
        assert r1 == r2

    def test_tool_result_inequality_different_success(self):
        r1 = ToolResult(success=True, output={}, error=None)
        r2 = ToolResult(success=False, output={}, error=None)
        assert r1 != r2

    def test_tool_result_inequality_different_output(self):
        r1 = ToolResult(success=True, output={"a": 1}, error=None)
        r2 = ToolResult(success=True, output={"a": 2}, error=None)
        assert r1 != r2

    def test_tool_result_inequality_different_error(self):
        r1 = ToolResult(success=False, output={}, error=None)
        r2 = ToolResult(success=False, output={}, error="err")
        assert r1 != r2

    def test_tool_result_repr(self):
        result = ToolResult(success=True, output={"k": "v"}, error=None)
        repr_str = repr(result)
        assert "ToolResult" in repr_str


class TestToolABC:
    def test_tool_is_abstract(self):
        assert inspect.isabstract(Tool)

    def test_tool_cannot_be_instantiated(self):
        with pytest.raises(TypeError):
            Tool()

    def test_tool_subclass_without_execute_cannot_be_instantiated(self):
        class _IncompleteTool(Tool):
            @property
            def name(self) -> str:
                return "incomplete"

            @property
            def schema(self) -> dict[str, Any]:
                return {"type": "object", "properties": {}}

        with pytest.raises(TypeError):
            _IncompleteTool()

    def test_tool_subclass_without_name_cannot_be_instantiated(self):
        class _NoNameTool(Tool):
            @property
            def schema(self) -> dict[str, Any]:
                return {"type": "object", "properties": {}}

            def execute(self, args: dict[str, Any]) -> ToolResult:
                return ToolResult(success=True, output={})

        with pytest.raises(TypeError):
            _NoNameTool()

    def test_tool_subclass_without_schema_cannot_be_instantiated(self):
        class _NoSchemaTool(Tool):
            @property
            def name(self) -> str:
                return "no_schema"

            def execute(self, args: dict[str, Any]) -> ToolResult:
                return ToolResult(success=True, output={})

        with pytest.raises(TypeError):
            _NoSchemaTool()

    def test_tool_subclass_with_all_members_can_be_instantiated(self):
        tool = _EchoTool()
        assert isinstance(tool, Tool)

    def test_tool_subclass_name_accessible(self):
        tool = _EchoTool()
        assert tool.name == "echo"

    def test_tool_subclass_schema_accessible(self):
        tool = _EchoTool()
        schema = tool.schema
        assert isinstance(schema, dict)
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "message" in schema["properties"]

    def test_tool_execute_is_abstract_method(self):
        assert hasattr(Tool, "execute")
        assert getattr(Tool.execute, "__isabstractmethod__", False) is True

    def test_tool_subclass_execute_returns_tool_result(self):
        tool = _EchoTool()
        result = tool.execute({"message": "hello"})
        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.output == {"echo": "hello"}

    def test_tool_subclass_execute_with_empty_args(self):
        tool = _EchoTool()
        result = tool.execute({})
        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.output == {"echo": ""}

    def test_tool_failing_subclass_returns_failed_result(self):
        tool = _FailingTool()
        result = tool.execute({})
        assert result.success is False
        assert result.error == "intentional failure"

    def test_tool_custom_name_subclass(self):
        tool = _CustomNameTool("custom_tool")
        assert tool.name == "custom_tool"
        assert isinstance(tool, Tool)


class TestToolRegistryRegistration:
    def test_register_single_tool(self):
        registry = ToolRegistry(Config())
        tool = _EchoTool()
        registry.register(tool)
        schemas = registry.get_schemas()
        assert len(schemas) == 1
        assert schemas[0] == tool.schema

    def test_register_multiple_tools(self):
        registry = ToolRegistry(Config())
        registry.register(_EchoTool())
        registry.register(_FailingTool())
        registry.register(_NoOpTool())
        schemas = registry.get_schemas()
        assert len(schemas) == 3

    def test_register_same_name_overwrites(self):
        registry = ToolRegistry(_test_config())
        first = _EchoTool()
        second = _CustomNameTool("echo")
        registry.register(first)
        registry.register(second)
        action = Action(tool_name="echo", args={"input": "overwritten"})
        result = registry.dispatch(action)
        assert result.output == {"received": "overwritten"}

    def test_register_allows_dispatch_by_name(self):
        registry = ToolRegistry(_test_config())
        registry.register(_EchoTool())
        action = Action(tool_name="echo", args={"message": "hi"})
        result = registry.dispatch(action)
        assert result.success is True
        assert result.output == {"echo": "hi"}

    def test_register_returns_none(self):
        registry = ToolRegistry(Config())
        ret = registry.register(_EchoTool())
        assert ret is None


class TestToolRegistryDispatch:
    def test_dispatch_calls_execute_with_action_args(self):
        registry = ToolRegistry(_test_config())
        registry.register(_EchoTool())
        action = Action(
            tool_name="echo",
            args={"message": "dispatched"},
        )
        result = registry.dispatch(action)
        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.output == {"echo": "dispatched"}

    def test_dispatch_returns_tool_result(self):
        registry = ToolRegistry(_test_config())
        registry.register(_EchoTool())
        action = Action(tool_name="echo", args={"message": "test"})
        result = registry.dispatch(action)
        assert isinstance(result, ToolResult)

    def test_dispatch_unregistered_tool_raises(self):
        registry = ToolRegistry(_test_config())
        action = Action(tool_name="nonexistent", args={})
        with pytest.raises(KeyError):
            registry.dispatch(action)

    def test_dispatch_with_empty_args(self):
        registry = ToolRegistry(_test_config())
        registry.register(_NoOpTool())
        action = Action(tool_name="noop", args={})
        result = registry.dispatch(action)
        assert result.success is True
        assert result.output == {}

    def test_dispatch_passes_args_correctly(self):
        registry = ToolRegistry(_test_config())
        registry.register(_CustomNameTool("custom"))
        action = Action(
            tool_name="custom",
            args={"input": "passed_value"},
        )
        result = registry.dispatch(action)
        assert result.output == {"received": "passed_value"}

    def test_dispatch_failing_tool_returns_failed_result(self):
        registry = ToolRegistry(_test_config())
        registry.register(_FailingTool())
        action = Action(tool_name="fail_tool", args={})
        result = registry.dispatch(action)
        assert result.success is False
        assert result.error == "intentional failure"

    def test_dispatch_preserves_action_raw_tool_call(self):
        registry = ToolRegistry(_test_config())
        registry.register(_EchoTool())
        raw = {"id": "call_abc", "type": "function"}
        action = Action(
            tool_name="echo",
            args={"message": "raw"},
            raw_tool_call=raw,
        )
        result = registry.dispatch(action)
        assert result.success is True
        assert result.output == {"echo": "raw"}


class TestToolRegistryWhitelist:
    def test_is_enabled_returns_true_for_enabled_tool(self):
        config = Config(enabled_tools=["echo", "read_file"])
        registry = ToolRegistry(config)
        assert registry.is_enabled("echo") is True

    def test_is_enabled_returns_false_for_disabled_tool(self):
        config = Config(enabled_tools=["read_file", "write_file"])
        registry = ToolRegistry(config)
        assert registry.is_enabled("echo") is False

    def test_is_enabled_with_default_config(self):
        registry = ToolRegistry(Config())
        assert registry.is_enabled("write_file") is True
        assert registry.is_enabled("read_file") is True
        assert registry.is_enabled("list_files") is True
        assert registry.is_enabled("run_tests") is True
        assert registry.is_enabled("run_command") is True
        assert registry.is_enabled("finish") is True

    def test_is_enabled_returns_false_for_unknown_tool_default_config(self):
        registry = ToolRegistry(Config())
        assert registry.is_enabled("echo") is False
        assert registry.is_enabled("nonexistent") is False

    def test_is_enabled_returns_bool(self):
        registry = ToolRegistry(Config())
        result = registry.is_enabled("write_file")
        assert isinstance(result, bool)

    def test_dispatch_disabled_tool_raises(self):
        config = Config(enabled_tools=["read_file"])
        registry = ToolRegistry(config)
        registry.register(_EchoTool())
        action = Action(tool_name="echo", args={"message": "hi"})
        with pytest.raises(PermissionError):
            registry.dispatch(action)

    def test_dispatch_enabled_tool_succeeds(self):
        config = Config(enabled_tools=["echo"])
        registry = ToolRegistry(config)
        registry.register(_EchoTool())
        action = Action(tool_name="echo", args={"message": "ok"})
        result = registry.dispatch(action)
        assert result.success is True
        assert result.output == {"echo": "ok"}

    def test_dispatch_respects_whitelist_not_registration(self):
        config = Config(enabled_tools=["read_file"])
        registry = ToolRegistry(config)
        registry.register(_EchoTool())
        assert registry.is_enabled("echo") is False
        action = Action(tool_name="echo", args={})
        with pytest.raises(PermissionError):
            registry.dispatch(action)

    def test_is_enabled_with_empty_enabled_tools(self):
        config = Config(enabled_tools=[])
        registry = ToolRegistry(config)
        assert registry.is_enabled("echo") is False
        assert registry.is_enabled("write_file") is False

    def test_dispatch_default_config_rejects_non_whitelisted_tool(self):
        """SPEC §3.6.1: enabled_tools is the whitelist for dispatch()."""
        registry = ToolRegistry(Config())
        registry.register(_EchoTool())
        action = Action(tool_name="echo", args={})
        with pytest.raises(PermissionError):
            registry.dispatch(action)


class TestToolRegistryGetSchemas:
    def test_get_schemas_empty_registry(self):
        registry = ToolRegistry(Config())
        schemas = registry.get_schemas()
        assert schemas == []
        assert isinstance(schemas, list)

    def test_get_schemas_single_tool(self):
        registry = ToolRegistry(Config())
        registry.register(_EchoTool())
        schemas = registry.get_schemas()
        assert len(schemas) == 1
        assert schemas[0] == _EchoTool().schema

    def test_get_schemas_multiple_tools(self):
        registry = ToolRegistry(Config())
        registry.register(_EchoTool())
        registry.register(_FailingTool())
        registry.register(_NoOpTool())
        schemas = registry.get_schemas()
        assert len(schemas) == 3

    def test_get_schemas_matches_tool_declarations(self):
        registry = ToolRegistry(Config())
        echo = _EchoTool()
        noop = _NoOpTool()
        registry.register(echo)
        registry.register(noop)
        schemas = registry.get_schemas()
        assert echo.schema in schemas
        assert noop.schema in schemas

    def test_get_schemas_returns_list_of_dicts(self):
        registry = ToolRegistry(Config())
        registry.register(_EchoTool())
        schemas = registry.get_schemas()
        assert isinstance(schemas, list)
        for schema in schemas:
            assert isinstance(schema, dict)

    def test_get_schemas_contains_name_and_properties(self):
        registry = ToolRegistry(Config())
        registry.register(_EchoTool())
        schemas = registry.get_schemas()
        echo_schema = schemas[0]
        assert "type" in echo_schema
        assert echo_schema["type"] == "object"
        assert "properties" in echo_schema
        assert "required" in echo_schema

    def test_get_schemas_after_reregistration_reflects_latest(self):
        registry = ToolRegistry(Config())
        registry.register(_EchoTool())
        registry.register(_CustomNameTool("echo"))
        schemas = registry.get_schemas()
        assert len(schemas) == 1
        assert schemas[0] == _CustomNameTool("echo").schema


class TestToolRegistryEdgeCases:
    def test_empty_registry_dispatch_raises(self):
        registry = ToolRegistry(Config())
        action = Action(tool_name="anything", args={})
        with pytest.raises(KeyError):
            registry.dispatch(action)

    def test_empty_registry_get_schemas(self):
        registry = ToolRegistry(Config())
        assert registry.get_schemas() == []

    def test_empty_registry_is_enabled(self):
        registry = ToolRegistry(Config())
        assert registry.is_enabled("anything") is False

    def test_dispatch_with_empty_args_to_echo(self):
        registry = ToolRegistry(_test_config())
        registry.register(_EchoTool())
        action = Action(tool_name="echo", args={})
        result = registry.dispatch(action)
        assert result.success is True
        assert result.output == {"echo": ""}

    def test_tool_result_with_none_error(self):
        result = ToolResult(success=True, output={"data": 1}, error=None)
        assert result.error is None
        assert result.success is True

    def test_multiple_tools_registered_dispatch_each(self):
        registry = ToolRegistry(_test_config())
        registry.register(_EchoTool())
        registry.register(_FailingTool())
        registry.register(_NoOpTool())

        echo_result = registry.dispatch(
            Action(tool_name="echo", args={"message": "m1"})
        )
        assert echo_result.output == {"echo": "m1"}

        fail_result = registry.dispatch(
            Action(tool_name="fail_tool", args={})
        )
        assert fail_result.success is False
        assert fail_result.error == "intentional failure"

        noop_result = registry.dispatch(
            Action(tool_name="noop", args={})
        )
        assert noop_result.success is True
        assert noop_result.output == {}

    def test_registry_with_custom_config_whitelist(self):
        config = Config(enabled_tools=["echo", "noop"])
        registry = ToolRegistry(config)
        registry.register(_EchoTool())
        registry.register(_NoOpTool())
        registry.register(_FailingTool())

        assert registry.is_enabled("echo") is True
        assert registry.is_enabled("noop") is True
        assert registry.is_enabled("fail_tool") is False

    def test_dispatch_action_with_raw_tool_call(self):
        registry = ToolRegistry(_test_config())
        registry.register(_EchoTool())
        raw = {"id": "call_xyz", "type": "function", "name": "echo"}
        action = Action(
            tool_name="echo",
            args={"message": "raw_call"},
            raw_tool_call=raw,
        )
        result = registry.dispatch(action)
        assert result.success is True
        assert result.output == {"echo": "raw_call"}

    def test_tool_result_success_only_required(self):
        result = ToolResult(success=True, output={})
        assert result.success is True
        assert result.output == {}
        assert result.error is None

    def test_registry_register_then_check_schemas_count(self):
        registry = ToolRegistry(Config())
        assert len(registry.get_schemas()) == 0
        registry.register(_EchoTool())
        assert len(registry.get_schemas()) == 1
        registry.register(_NoOpTool())
        assert len(registry.get_schemas()) == 2

    def test_dispatch_propagates_execute_exception(self):
        """dispatch() does not catch exceptions from tool.execute()."""
        registry = ToolRegistry(_test_config())
        registry.register(_RaisingTool())
        action = Action(tool_name="raiser", args={})
        with pytest.raises(RuntimeError, match="unexpected internal error"):
            registry.dispatch(action)
