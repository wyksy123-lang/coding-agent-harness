from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from harness.agent_loop import AgentResult
from harness.cli import CLIDependencies, build_tool_registry, main
from harness.models import Action, Config, StopReason


@dataclass
class FakeCredentials:
    key: str | None = "fake-api-key"
    status_value: str = "fake-****...1234"

    def __post_init__(self) -> None:
        self.calls: list[str] = []

    def setup(self) -> None:
        self.calls.append("setup")

    def status(self) -> str:
        self.calls.append("status")
        return self.status_value

    def update(self) -> None:
        self.calls.append("update")

    def clear(self) -> None:
        self.calls.append("clear")

    def get_key(self) -> str | None:
        self.calls.append("get_key")
        return self.key


class FakeAgentLoop:
    def __init__(self) -> None:
        self.requirements: list[str] = []

    def run(self, requirement: str) -> AgentResult:
        self.requirements.append(requirement)
        return AgentResult(status=StopReason.PASS, rounds=[], output_files=[])


def test_run_loads_config_and_invokes_agent_loop_with_requested_file(
    tmp_path: Path, capsys: Any
) -> None:
    config = Config(max_rounds=1, target_directory=str(tmp_path))
    loaded_paths: list[Path] = []
    agent_loop = FakeAgentLoop()
    factory_inputs: list[tuple[Config, str]] = []

    def load_config(path: str | Path) -> Config:
        loaded_paths.append(Path(path))
        return config

    def make_agent_loop(config_arg: Config, api_key: str) -> FakeAgentLoop:
        factory_inputs.append((config_arg, api_key))
        return agent_loop

    config_path = tmp_path / "harness.yaml"
    exit_code = main(
        ["run", "implement the feature", "--config", str(config_path)],
        dependencies=CLIDependencies(
            load_config=load_config,
            make_credentials=lambda: FakeCredentials(key="fake-live-key"),
            make_agent_loop=make_agent_loop,
        ),
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert loaded_paths == [config_path]
    assert factory_inputs == [(config, "fake-live-key")]
    assert agent_loop.requirements == ["implement the feature"]
    assert "PASS" in output


def test_run_uses_default_config_path_when_omitted(capsys: Any) -> None:
    loaded_paths: list[Path] = []

    def load_config(path: str | Path) -> Config:
        loaded_paths.append(Path(path))
        return Config()

    exit_code = main(
        ["run", "use defaults"],
        dependencies=CLIDependencies(
            load_config=load_config,
            make_credentials=lambda: FakeCredentials(key="fake-live-key"),
            make_agent_loop=lambda _config, _api_key: FakeAgentLoop(),
        ),
    )

    assert exit_code == 0
    assert loaded_paths == [Path("harness.yaml")]
    assert "PASS" in capsys.readouterr().out


def test_run_without_key_suggests_setup_and_does_not_load_config(
    capsys: Any,
) -> None:
    load_called = False
    agent_loop_called = False

    def load_config(_path: str | Path) -> Config:
        nonlocal load_called
        load_called = True
        return Config()

    def make_agent_loop(_config: Config, _api_key: str) -> FakeAgentLoop:
        nonlocal agent_loop_called
        agent_loop_called = True
        return FakeAgentLoop()

    exit_code = main(
        ["run", "implement safely"],
        dependencies=CLIDependencies(
            load_config=load_config,
            make_credentials=lambda: FakeCredentials(key=None),
            make_agent_loop=make_agent_loop,
        ),
    )

    output = capsys.readouterr().err
    assert exit_code == 1
    assert "harness key setup" in output
    assert not load_called
    assert not agent_loop_called


def test_key_status_prints_masked_status(capsys: Any) -> None:
    credentials = FakeCredentials(status_value="fake-****...1234")

    exit_code = main(
        ["key", "status"],
        dependencies=CLIDependencies(
            load_config=lambda _path: Config(),
            make_credentials=lambda: credentials,
            make_agent_loop=lambda _config, _api_key: FakeAgentLoop(),
        ),
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "fake-****...1234" in output
    assert "fake-api-key" not in output
    assert credentials.calls == ["status"]


def test_key_setup_update_and_clear_call_credential_manager(capsys: Any) -> None:
    credentials = FakeCredentials()

    for command in ("setup", "update", "clear"):
        exit_code = main(
            ["key", command],
            dependencies=CLIDependencies(
                load_config=lambda _path: Config(),
                make_credentials=lambda: credentials,
                make_agent_loop=lambda _config, _api_key: FakeAgentLoop(),
            ),
        )
        assert exit_code == 0

    capsys.readouterr()
    assert credentials.calls == ["setup", "update", "clear"]


def test_default_tool_registry_exposes_finish_tool(tmp_path: Path) -> None:
    registry = build_tool_registry(Config(target_directory=str(tmp_path)))

    finish_schemas = [
        schema for schema in registry.get_schemas() if schema.get("name") == "finish"
    ]
    assert finish_schemas == [
        {"name": "finish", "type": "object", "properties": {}, "required": []}
    ]
    assert registry.dispatch(Action(tool_name="finish", args={})).success is True
