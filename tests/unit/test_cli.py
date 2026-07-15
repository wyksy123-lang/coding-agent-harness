from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from harness.agent_loop import AgentResult
from harness.cli import CLIDependencies, build_parser, build_tool_registry, main
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
    def __init__(self, status: StopReason = StopReason.PASS) -> None:
        self.requirements: list[str] = []
        self._status = status

    def run(self, requirement: str) -> AgentResult:
        self.requirements.append(requirement)
        return AgentResult(status=self._status, rounds=[], output_files=[])


def test_run_parser_accepts_flash_and_pro_model_aliases() -> None:
    parser = build_parser()

    flash_args = parser.parse_args(["run", "task", "--model", "flash"])
    pro_args = parser.parse_args(["run", "task", "--model", "pro"])

    assert flash_args.model == "flash"
    assert pro_args.model == "pro"


def test_run_rejects_invalid_model_before_loading_config_or_agent_loop(
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
        ["run", "task", "--model", "invalid"],
        dependencies=CLIDependencies(
            load_config=load_config,
            make_credentials=lambda: FakeCredentials(key="fake-live-key"),
            make_agent_loop=make_agent_loop,
        ),
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "flash" in captured.err
    assert "pro" in captured.err
    assert not load_called
    assert not agent_loop_called


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


def test_run_without_model_preserves_loaded_config_model(capsys: Any) -> None:
    config = Config(model="configured-model")
    factory_inputs: list[tuple[Config, str]] = []

    def make_agent_loop(config_arg: Config, api_key: str) -> FakeAgentLoop:
        factory_inputs.append((config_arg, api_key))
        return FakeAgentLoop()

    exit_code = main(
        ["run", "use configured model"],
        dependencies=CLIDependencies(
            load_config=lambda _path: config,
            make_credentials=lambda: FakeCredentials(key="fake-live-key"),
            make_agent_loop=make_agent_loop,
        ),
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert len(factory_inputs) == 1
    assert factory_inputs[0][0].model == "configured-model"
    assert config.model == "configured-model"
    assert "model: configured-model" in output


def test_run_model_flash_overrides_config_for_current_run_only(
    capsys: Any,
) -> None:
    config = Config(model="configured-model")
    agent_loop = FakeAgentLoop()
    factory_inputs: list[tuple[Config, str]] = []

    def make_agent_loop(config_arg: Config, api_key: str) -> FakeAgentLoop:
        factory_inputs.append((config_arg, api_key))
        return agent_loop

    exit_code = main(
        ["run", "use flash", "--model", "flash"],
        dependencies=CLIDependencies(
            load_config=lambda _path: config,
            make_credentials=lambda: FakeCredentials(key="fake-live-key"),
            make_agent_loop=make_agent_loop,
        ),
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert len(factory_inputs) == 1
    assert factory_inputs[0][0].model == "deepseek-v4-flash"
    assert factory_inputs[0][0] is not config
    assert config.model == "configured-model"
    assert agent_loop.requirements == ["use flash"]
    assert "model: deepseek-v4-flash" in output
    assert "fake-live-key" not in output


def test_run_model_pro_overrides_config_for_current_run_only(
    capsys: Any,
) -> None:
    config = Config(model="configured-model")
    factory_inputs: list[tuple[Config, str]] = []

    def make_agent_loop(config_arg: Config, api_key: str) -> FakeAgentLoop:
        factory_inputs.append((config_arg, api_key))
        return FakeAgentLoop()

    exit_code = main(
        ["run", "use pro", "--model", "pro"],
        dependencies=CLIDependencies(
            load_config=lambda _path: config,
            make_credentials=lambda: FakeCredentials(key="fake-live-key"),
            make_agent_loop=make_agent_loop,
        ),
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert len(factory_inputs) == 1
    assert factory_inputs[0][0].model == "deepseek-v4-pro"
    assert config.model == "configured-model"
    assert "model: deepseek-v4-pro" in output


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


def test_run_web_model_flash_passes_override_to_web_runner(
    tmp_path: Path,
    capsys: Any,
) -> None:
    config = Config(model="configured-model", target_directory=str(tmp_path))
    calls: list[tuple[str, Config, str]] = []
    make_agent_loop_called = False

    def make_agent_loop(_config: Config, _api_key: str) -> FakeAgentLoop:
        nonlocal make_agent_loop_called
        make_agent_loop_called = True
        return FakeAgentLoop()

    def run_webui(
        requirement: str,
        config_arg: Config,
        api_key: str,
        make_agent_loop: Any,
    ) -> AgentResult:
        calls.append((requirement, config_arg, api_key))
        assert callable(make_agent_loop)
        return AgentResult(status=StopReason.PASS, rounds=[], output_files=[])

    exit_code = main(
        ["run", "show flash ui", "--model", "flash", "--web"],
        dependencies=CLIDependencies(
            load_config=lambda _path: config,
            make_credentials=lambda: FakeCredentials(key="fake-live-key"),
            make_agent_loop=make_agent_loop,
            run_webui=run_webui,
        ),
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert len(calls) == 1
    assert calls[0][1].model == "deepseek-v4-flash"
    assert config.model == "configured-model"
    assert not make_agent_loop_called
    assert "model: deepseek-v4-flash" in output


def test_run_web_model_pro_accepts_web_before_model_order(
    tmp_path: Path,
    capsys: Any,
) -> None:
    config = Config(model="configured-model", target_directory=str(tmp_path))
    calls: list[tuple[str, Config, str]] = []

    def run_webui(
        requirement: str,
        config_arg: Config,
        api_key: str,
        make_agent_loop: Any,
    ) -> AgentResult:
        calls.append((requirement, config_arg, api_key))
        assert callable(make_agent_loop)
        return AgentResult(status=StopReason.PASS, rounds=[], output_files=[])

    exit_code = main(
        ["run", "show pro ui", "--web", "--model", "pro"],
        dependencies=CLIDependencies(
            load_config=lambda _path: config,
            make_credentials=lambda: FakeCredentials(key="fake-live-key"),
            make_agent_loop=lambda _config, _api_key: FakeAgentLoop(),
            run_webui=run_webui,
        ),
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert len(calls) == 1
    assert calls[0][1].model == "deepseek-v4-pro"
    assert config.model == "configured-model"
    assert "model: deepseek-v4-pro" in output


def test_run_web_invokes_local_web_runner_with_loaded_config(
    tmp_path: Path,
    capsys: Any,
) -> None:
    config = Config(max_rounds=1, target_directory=str(tmp_path))
    config_path = tmp_path / "harness.yaml"
    calls: list[tuple[str, Config, str]] = []

    def run_webui(
        requirement: str,
        config_arg: Config,
        api_key: str,
        make_agent_loop: Any,
    ) -> AgentResult:
        calls.append((requirement, config_arg, api_key))
        assert callable(make_agent_loop)
        return AgentResult(status=StopReason.PASS, rounds=[], output_files=[])

    exit_code = main(
        ["run", "show ui", "--web", "--config", str(config_path)],
        dependencies=CLIDependencies(
            load_config=lambda path: config if Path(path) == config_path else Config(),
            make_credentials=lambda: FakeCredentials(key="fake-live-key"),
            make_agent_loop=lambda _config, _api_key: FakeAgentLoop(),
            run_webui=run_webui,
        ),
    )

    assert exit_code == 0
    assert calls == [("show ui", config, "fake-live-key")]
    assert "PASS" in capsys.readouterr().out


def test_run_web_does_not_accept_public_host_option(capsys: Any) -> None:
    exit_code = main(
        ["run", "show ui", "--web", "--host", "0.0.0.0"],
        dependencies=CLIDependencies(
            load_config=lambda _path: Config(),
            make_credentials=lambda: FakeCredentials(key="fake-live-key"),
            make_agent_loop=lambda _config, _api_key: FakeAgentLoop(),
        ),
    )

    assert exit_code == 2
    assert "host" in capsys.readouterr().err


def test_run_help_lists_model_alias_choices(capsys: Any) -> None:
    exit_code = main(["run", "--help"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "--model {flash,pro}" in output


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


def test_run_returns_nonzero_for_llm_error_without_traceback(capsys: Any) -> None:
    exit_code = main(
        ["run", "fail safely"],
        dependencies=CLIDependencies(
            load_config=lambda _path: Config(),
            make_credentials=lambda: FakeCredentials(key="fake-live-key"),
            make_agent_loop=lambda _config, _api_key: FakeAgentLoop(
                status=StopReason.LLM_ERROR
            ),
        ),
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "LLM_ERROR" in captured.out
    assert "Traceback" not in captured.err


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


def test_default_tool_registry_exposes_finish_as_llm_function_tool(tmp_path: Path) -> None:
    registry = build_tool_registry(Config(target_directory=str(tmp_path)))

    finish_schemas = [
        schema
        for schema in registry.get_llm_schemas()
        if schema["function"]["name"] == "finish"
    ]

    assert finish_schemas == [
        {
            "type": "function",
            "function": {
                "name": "finish",
                "description": "finish",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        }
    ]
