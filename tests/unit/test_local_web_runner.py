from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from harness.agent_loop import AgentResult
from harness.models import Config, StopReason
from webui.local_runner import run_with_local_webui


@dataclass
class FakeServer:
    app: Any
    host: str
    port: int
    started: bool = False
    stopped: bool = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True


class FakeAgentLoop:
    def __init__(self, result: AgentResult) -> None:
        self.result = result
        self.requirements: list[str] = []

    def run(self, requirement: str) -> AgentResult:
        self.requirements.append(requirement)
        return self.result


def test_local_web_runner_binds_loopback_and_injects_webui_adapters() -> None:
    config = Config()
    result = AgentResult(status=StopReason.PASS, rounds=[], output_files=[])
    agent_loop = FakeAgentLoop(result)
    servers: list[FakeServer] = []
    factory_kwargs: dict[str, Any] = {}

    def server_factory(app: Any, host: str, port: int) -> FakeServer:
        server = FakeServer(app=app, host=host, port=port)
        servers.append(server)
        return server

    def make_agent_loop(config_arg: Config, api_key: str, **kwargs: Any) -> FakeAgentLoop:
        factory_kwargs.update(kwargs)
        assert config_arg is config
        assert api_key == "fake-key"
        return agent_loop

    actual = run_with_local_webui(
        "do work",
        config,
        "fake-key",
        make_agent_loop,
        server_factory=server_factory,
        wait_until_ready=lambda _url: None,
        open_browser=lambda _url: True,
    )

    assert actual is result
    assert servers[0].host == "127.0.0.1"
    assert servers[0].port == 8000
    assert servers[0].app.state.webui_state.mode == "live"
    assert "event_sink" in factory_kwargs
    assert "approval_broker" in factory_kwargs
    assert agent_loop.requirements == ["do work"]
    assert servers[0].stopped is True


def test_local_web_runner_opens_browser_after_readiness() -> None:
    events: list[str] = []

    def server_factory(app: Any, host: str, port: int) -> FakeServer:
        server = FakeServer(app=app, host=host, port=port)
        original_start = server.start

        def start() -> None:
            events.append("start")
            original_start()

        server.start = start
        return server

    def wait_until_ready(url: str) -> None:
        assert url == "http://127.0.0.1:8000/"
        events.append("ready")

    def open_browser(url: str) -> bool:
        assert url == "http://127.0.0.1:8000/"
        events.append("browser")
        return True

    run_with_local_webui(
        "do work",
        Config(),
        "fake-key",
        lambda _config, _api_key, **_kwargs: FakeAgentLoop(
            AgentResult(status=StopReason.PASS, rounds=[], output_files=[])
        ),
        server_factory=server_factory,
        wait_until_ready=wait_until_ready,
        open_browser=open_browser,
    )

    assert events == ["start", "ready", "browser"]


def test_local_web_runner_stops_server_when_agent_loop_fails() -> None:
    server = FakeServer(app=None, host="", port=0)

    class FailingAgentLoop:
        def run(self, _requirement: str) -> AgentResult:
            raise RuntimeError("boom")

    try:
        run_with_local_webui(
            "do work",
            Config(),
            "fake-key",
            lambda _config, _api_key, **_kwargs: FailingAgentLoop(),
            server_factory=lambda app, host, port: server,
            wait_until_ready=lambda _url: None,
            open_browser=lambda _url: True,
        )
    except RuntimeError as exc:
        assert str(exc) == "boom"

    assert server.stopped is True
