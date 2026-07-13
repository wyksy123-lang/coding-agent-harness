from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast

from harness.agent_loop import AgentResult
from harness.config.loader import ConfigError, ConfigLoader
from harness.credentials.manager import CredentialManager
from harness.models import Config


class CredentialManagerProtocol(Protocol):
    def setup(self) -> None: ...

    def status(self) -> str: ...

    def update(self) -> None: ...

    def clear(self) -> None: ...

    def get_key(self) -> str | None: ...


class AgentLoopProtocol(Protocol):
    def run(self, requirement: str) -> AgentResult: ...


LoadConfig = Callable[[str | Path], Config]
CredentialFactory = Callable[[], CredentialManagerProtocol]
AgentLoopFactory = Callable[[Config, str], AgentLoopProtocol]


def _default_agent_loop_factory(config: Config, api_key: str) -> AgentLoopProtocol:
    from harness.agent_loop import AgentLoop
    from harness.llm.deepseek import DeepSeekClient
    from harness.tools import (
        ListFilesTool,
        ReadFileTool,
        RunCommandTool,
        RunTestsTool,
        ToolRegistry,
        WriteFileTool,
    )

    llm_client = DeepSeekClient(
        api_key=api_key,
        model=config.model,
        temperature=config.temperature,
        timeout=config.llm_timeout,
        retry_count=config.llm_retry_count,
    )
    registry = ToolRegistry(config)
    registry.register(WriteFileTool(config.target_directory))
    registry.register(ReadFileTool(config.target_directory))
    registry.register(ListFilesTool(config.target_directory))
    registry.register(
        RunCommandTool(
            config.target_directory,
            config.dangerous_command_patterns,
            timeout=config.pytest_timeout,
        )
    )
    registry.register(
        RunTestsTool(
            config.target_directory,
            config.test_command,
            pytest_timeout=config.pytest_timeout,
        )
    )
    return AgentLoop(config, llm_client, registry)


@dataclass(frozen=True)
class CLIDependencies:
    load_config: LoadConfig = ConfigLoader.load
    make_credentials: CredentialFactory = CredentialManager
    make_agent_loop: AgentLoopFactory = _default_agent_loop_factory


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="harness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("requirement")
    run_parser.add_argument("--config", default="harness.yaml")

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
    args = parser.parse_args(argv)
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
        print("API key not configured. Run `harness key setup`.")
        return 1

    config_path = cast(str, args.config)
    try:
        config = dependencies.load_config(config_path)
    except ConfigError as exc:
        print(f"Config error: {exc}")
        return 2

    requirement = cast(str, args.requirement)
    result = dependencies.make_agent_loop(config, api_key).run(requirement)
    print(f"status: {result.status.value}")
    if result.output_files:
        print("output_files:")
        for output_file in result.output_files:
            print(f"- {output_file}")
    return 0


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
