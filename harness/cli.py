from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, Protocol, cast

from harness.config.loader import ConfigError, ConfigLoader
from harness.credentials.manager import CredentialManager
from harness.models import Config


class CredentialManagerProtocol(Protocol):
    def setup(self) -> None: ...

    def status(self) -> str: ...

    def update(self) -> None: ...

    def clear(self) -> None: ...

    def get_key(self) -> str | None: ...


class AgentRunResultProtocol(Protocol):
    @property
    def status(self) -> object: ...

    @property
    def output_files(self) -> list[str]: ...


class AgentLoopProtocol(Protocol):
    def run(self, requirement: str) -> AgentRunResultProtocol: ...


LoadConfig = Callable[[str | Path], Config]
CredentialFactory = Callable[[], CredentialManagerProtocol]
class AgentLoopFactory(Protocol):
    def __call__(
        self,
        config: Config,
        api_key: str,
        **kwargs: Any,
    ) -> AgentLoopProtocol: ...


RunWebUI = Callable[[str, Config, str, AgentLoopFactory], AgentRunResultProtocol]
ToolConstructor = Callable[..., object]


class ToolRegistryProtocol(Protocol):
    def register(self, tool: object) -> None: ...

    def get_schemas(self) -> list[dict[str, Any]]: ...

    def dispatch(self, action: object) -> Any: ...


class _FinishTool:
    @property
    def name(self) -> str:
        return "finish"

    @property
    def schema(self) -> dict[str, Any]:
        return {"name": "finish", "type": "object", "properties": {}, "required": []}

    def execute(self, args: dict[str, Any]) -> object:
        tool_result = cast(
            Callable[..., object],
            import_module("harness.tools.base").ToolResult,
        )
        return tool_result(success=True, output={})


def _tool_class(module_name: str, class_name: str) -> ToolConstructor:
    module = import_module(module_name)
    return cast(ToolConstructor, getattr(module, class_name))


def build_tool_registry(config: Config) -> ToolRegistryProtocol:
    tool_registry = cast(
        Callable[[Config], ToolRegistryProtocol],
        import_module("harness.tools.base").ToolRegistry,
    )
    write_file_tool = _tool_class("harness.tools.file_ops", "WriteFileTool")
    read_file_tool = _tool_class("harness.tools.file_ops", "ReadFileTool")
    list_files_tool = _tool_class("harness.tools.file_ops", "ListFilesTool")
    run_command_tool = _tool_class("harness.tools.shell", "RunCommandTool")
    run_tests_tool = _tool_class("harness.tools.shell", "RunTestsTool")

    registry = tool_registry(config)
    registry.register(write_file_tool(config.target_directory))
    registry.register(read_file_tool(config.target_directory))
    registry.register(list_files_tool(config.target_directory))
    registry.register(
        run_command_tool(
            config.target_directory,
            config.dangerous_command_patterns,
            timeout=config.pytest_timeout,
        )
    )
    registry.register(
        run_tests_tool(
            config.target_directory,
            config.test_command,
            pytest_timeout=config.pytest_timeout,
        )
    )
    registry.register(_FinishTool())
    return registry


def _default_agent_loop_factory(
    config: Config,
    api_key: str,
    **kwargs: Any,
) -> AgentLoopProtocol:
    from harness.llm.deepseek import DeepSeekClient

    agent_loop = cast(
        Callable[..., AgentLoopProtocol],
        import_module("harness.agent_loop").AgentLoop,
    )
    llm_client = DeepSeekClient(
        api_key=api_key,
        model=config.model,
        temperature=config.temperature,
        timeout=config.llm_timeout,
        retry_count=config.llm_retry_count,
    )
    return agent_loop(
        config,
        llm_client,
        cast(Any, build_tool_registry(config)),
        **kwargs,
    )


def _default_run_webui(
    requirement: str,
    config: Config,
    api_key: str,
    make_agent_loop: AgentLoopFactory,
) -> AgentRunResultProtocol:
    from webui.local_runner import run_with_local_webui

    return run_with_local_webui(requirement, config, api_key, make_agent_loop)


@dataclass(frozen=True)
class CLIDependencies:
    load_config: LoadConfig = ConfigLoader.load
    make_credentials: CredentialFactory = CredentialManager
    make_agent_loop: AgentLoopFactory = _default_agent_loop_factory
    run_webui: RunWebUI = _default_run_webui


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="harness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("requirement")
    run_parser.add_argument("--config", default="harness.yaml")
    run_parser.add_argument("--web", action="store_true")

    key_parser = subparsers.add_parser("key")
    key_subparsers = key_parser.add_subparsers(dest="key_command", required=True)
    for command in ("setup", "status", "update", "clear"):
        key_subparsers.add_parser(command)

    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    dependencies: CLIDependencies | None = None,
) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 2
    deps = dependencies or CLIDependencies()

    command = cast(str, args.command)
    if command == "run":
        return _handle_run(args, deps)
    if command == "key":
        return _handle_key(args, deps)
    parser.error(f"unknown command: {command}")
    return 2


def _handle_run(args: argparse.Namespace, dependencies: CLIDependencies) -> int:
    credentials = dependencies.make_credentials()
    api_key = credentials.get_key()
    if api_key is None:
        print("API key not configured. Run `harness key setup`.", file=sys.stderr)
        return 1

    config_path = cast(str, args.config)
    try:
        config = dependencies.load_config(config_path)
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 2

    requirement = cast(str, args.requirement)
    if bool(getattr(args, "web", False)):
        result = dependencies.run_webui(
            requirement,
            config,
            api_key,
            dependencies.make_agent_loop,
        )
    else:
        result = dependencies.make_agent_loop(config, api_key).run(requirement)
    print(f"status: {_status_value(result.status)}")
    if result.output_files:
        print("output_files:")
        for output_file in result.output_files:
            print(f"- {output_file}")
    return 0


def _status_value(status: object) -> str:
    value = getattr(status, "value", status)
    return str(value)


def _handle_key(args: argparse.Namespace, dependencies: CLIDependencies) -> int:
    credentials = dependencies.make_credentials()
    key_command = cast(str, args.key_command)

    if key_command == "status":
        print(credentials.status())
        return 0
    if key_command == "setup":
        credentials.setup()
        print("API key setup complete.")
        return 0
    if key_command == "update":
        credentials.update()
        print("API key update complete.")
        return 0
    if key_command == "clear":
        credentials.clear()
        print("API key cleared.")
        return 0

    raise ValueError(f"unsupported key command: {key_command}")


def cli() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    cli()
