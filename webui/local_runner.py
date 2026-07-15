from __future__ import annotations

import socket
import threading
import time
import webbrowser
from collections.abc import Callable
from typing import Any, Protocol

import httpx
import uvicorn

from harness.models import Config
from webui.app import create_app

LOCAL_WEB_HOST = "127.0.0.1"
LOCAL_WEB_PORT = 8000
LOCAL_WEB_URL = f"http://{LOCAL_WEB_HOST}:{LOCAL_WEB_PORT}/"


class AgentRunResultProtocol(Protocol):
    @property
    def status(self) -> object: ...

    @property
    def output_files(self) -> list[str]: ...


class AgentLoopProtocol(Protocol):
    def run(self, requirement: str) -> AgentRunResultProtocol: ...


class AgentLoopFactory(Protocol):
    def __call__(
        self,
        config: Config,
        api_key: str,
        **kwargs: Any,
    ) -> AgentLoopProtocol: ...


class LocalServer(Protocol):
    def start(self) -> None: ...

    def stop(self) -> None: ...


ServerFactory = Callable[[Any, str, int], LocalServer]
OpenBrowser = Callable[[str], bool]
WaitUntilReady = Callable[[str], None]


def run_with_local_webui(
    requirement: str,
    config: Config,
    api_key: str,
    make_agent_loop: AgentLoopFactory,
    *,
    server_factory: ServerFactory | None = None,
    wait_until_ready: WaitUntilReady | None = None,
    open_browser: OpenBrowser | None = None,
    warning_sink: Callable[[str], None] | None = None,
) -> AgentRunResultProtocol:
    state_app = create_app(mode="live")
    state = state_app.state.webui_state
    server = (server_factory or _server_factory)(
        state_app,
        LOCAL_WEB_HOST,
        LOCAL_WEB_PORT,
    )
    wait = wait_until_ready or _wait_until_ready
    browser = open_browser or webbrowser.open
    warn = warning_sink or (lambda _message: None)

    server.start()
    try:
        wait(LOCAL_WEB_URL)
        try:
            browser(LOCAL_WEB_URL)
        except Exception as exc:
            warn(f"Could not open browser automatically: {exc}")
        agent_loop = make_agent_loop(
            config,
            api_key,
            event_sink=state.publish,
            approval_broker=state.approval_broker,
        )
        return agent_loop.run(requirement)
    finally:
        state.approval_broker.cancel_all()
        server.stop()


def _server_factory(app: Any, host: str, port: int) -> LocalServer:
    return UvicornThreadServer(app, host, port)


class UvicornThreadServer:
    def __init__(self, app: Any, host: str, port: int) -> None:
        self._app = app
        self._host = host
        self._port = port
        self._server: uvicorn.Server | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        _ensure_port_available(self._host, self._port)
        config = uvicorn.Config(
            self._app,
            host=self._host,
            port=self._port,
            log_level="info",
        )
        self._server = uvicorn.Server(config)
        self._thread = threading.Thread(target=self._server.run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server is not None:
            self._server.should_exit = True
        if self._thread is not None:
            self._thread.join(timeout=5)


def _ensure_port_available(host: str, port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError as exc:
            raise RuntimeError(f"WebUI port is unavailable: {host}:{port}") from exc


def _wait_until_ready(url: str) -> None:
    deadline = time.monotonic() + 10
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            response = httpx.get(url, timeout=1)
            if response.status_code == 200:
                return
        except httpx.HTTPError as exc:
            last_error = exc
        time.sleep(0.1)
    if last_error is not None:
        raise RuntimeError(f"WebUI did not become ready: {last_error}") from last_error
    raise RuntimeError("WebUI did not become ready")
