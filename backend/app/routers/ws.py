import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["realtime"])
log = logging.getLogger("blink.hub")

browsers: set[WebSocket] = set()


async def broadcast(text: str) -> None:
    dead = []
    for ws in list(browsers):
        try:
            await ws.send_text(text)
        except Exception:
            dead.append(ws)
    for ws in dead:
        browsers.discard(ws)


@router.websocket("/ws/cv")
async def cv_socket(ws: WebSocket):
    """CV connects here and sends events."""
    await ws.accept()
    log.info("CV connected")
    await broadcast(json.dumps({"type": "cv_connection", "connected": True}))
    try:
        while True:
            await broadcast(await ws.receive_text())
    except WebSocketDisconnect:
        pass
    finally:
        log.info("CV disconnected")
        await broadcast(json.dumps({"type": "cv_connection", "connected": False}))


@router.websocket("/ws/events")
async def events_socket(ws: WebSocket):
    """Browser connects here and receives events."""
    await ws.accept()
    browsers.add(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        browsers.discard(ws)