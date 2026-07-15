from __future__ import annotations

import asyncio
import json

from fastapi import WebSocket, WebSocketDisconnect

from webui.state import WebUIState

__all__ = ["WebSocketStatusEndpoint", "WebUIState"]


class WebSocketStatusEndpoint:
    def __init__(self, state: WebUIState) -> None:
        self._state = state

    async def handle(self, websocket: WebSocket) -> None:
        await websocket.accept()
        subscription = self._state.subscribe()
        try:
            while True:
                queue_task = asyncio.create_task(subscription.queue.get())
                receive_task = asyncio.create_task(websocket.receive_json())
                done, pending = await asyncio.wait(
                    {queue_task, receive_task},
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()

                if queue_task in done:
                    await websocket.send_json(queue_task.result())
                if receive_task in done:
                    try:
                        client_message = receive_task.result()
                    except json.JSONDecodeError:
                        await websocket.send_json(
                            {"type": "error", "detail": "invalid json message"}
                        )
                        continue
                    if (
                        isinstance(client_message, dict)
                        and client_message.get("type") == "ping"
                    ):
                        await websocket.send_json({"type": "pong"})
                    else:
                        snapshot = self._state.snapshot()
                        await websocket.send_json(
                            {
                                "type": "snapshot",
                                "snapshot": snapshot,
                                "timeline": snapshot.get("timeline", []),
                            }
                        )
        except WebSocketDisconnect:
            return
        finally:
            self._state.unsubscribe(subscription)
