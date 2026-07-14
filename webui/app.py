from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, WebSocket
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from harness.models import HITLRequest
from webui.websocket import WebSocketStatusEndpoint, WebUIState

_STATIC_DIR = Path(__file__).with_name("static")

__all__ = ["WebUIState", "app", "create_app"]


def create_app(state: WebUIState | None = None) -> FastAPI:
    webui_state = state or WebUIState()
    app = FastAPI(title="Coding Agent Harness")
    app.state.webui_state = webui_state
    app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")
    websocket_endpoint = WebSocketStatusEndpoint(webui_state)

    @app.get("/", response_class=HTMLResponse)
    async def root() -> FileResponse:
        return FileResponse(_STATIC_DIR / "index.html", media_type="text/html")

    @app.get("/api/status")
    async def get_status() -> dict[str, Any]:
        return webui_state.snapshot()

    @app.post("/api/hitl/{request_id}")
    async def decide_hitl(request_id: str, request: Request) -> dict[str, str]:
        try:
            payload = await request.json()
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="invalid json body") from exc
        if not isinstance(payload, dict):
            raise HTTPException(status_code=400, detail="decision is required")
        decision = payload.get("decision")
        if not isinstance(decision, str):
            raise HTTPException(status_code=400, detail="decision is required")
        try:
            hitl_request = webui_state.decide_hitl(request_id, decision)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="HITL request not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return _hitl_response(hitl_request)

    @app.websocket("/ws")
    async def websocket_status(websocket: WebSocket) -> None:
        await websocket_endpoint.handle(websocket)

    return app


def _hitl_response(request: HITLRequest) -> dict[str, str]:
    return {
        "request_id": request.request_id,
        "status": request.status.value,
        "decision": request.decision,
    }


app = create_app()
