"""
WebSocket Endpoints

Real-time bidirectional streaming over WebSocket.
"""

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from mycorrhizae import MycorrhizaeProtocol
from services.key_service import KeyServiceManager
from mycorrhizae.transports.websocket import WebSocketHandler


router = APIRouter()


async def get_protocol_dep() -> MycorrhizaeProtocol:
    from api.main import get_protocol
    return await get_protocol()


async def get_key_service_dep() -> KeyServiceManager:
    from api.main import get_key_service
    return await get_key_service()


@router.websocket("/subscribe")
async def websocket_subscribe(
    websocket: WebSocket,
    channels: str = Query("device.*.telemetry", description="Comma-separated channel patterns"),
):
    """
    Subscribe to channels via WebSocket.

    Query params:
    - channels: Comma-separated patterns, e.g. device.*.telemetry,device.*.event

    Optional: Send JSON {"type": "auth", "api_key": "..."} after connect for scoped access.

    Messages are sent as JSON: {"event": "message", "data": {...}, "id": "..."}
    """
    await websocket.accept()

    api_key_id = None
    try:
        data = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
        msg = json.loads(data) if data else {}
        if msg.get("type") == "auth" and msg.get("api_key"):
            key_svc = await get_key_service_dep()
            result = await key_svc.validate_key(
                raw_key=msg["api_key"],
                required_scopes=["read", "channel:subscribe"],
            )
            if result.valid and result.key:
                api_key_id = str(result.key.id)
    except (json.JSONDecodeError, KeyError, asyncio.TimeoutError):
        pass
    except Exception:
        pass

    channel_patterns = [p.strip() for p in channels.split(",") if p.strip()]
    if not channel_patterns:
        channel_patterns = ["device.*.telemetry"]

    proto = await get_protocol_dep()
    handler = WebSocketHandler(
        websocket=websocket,
        protocol=proto,
        channel_patterns=channel_patterns,
        api_key_id=api_key_id,
    )

    try:
        await handler.run()
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.close(code=1011, reason=str(e)[:123])
        except Exception:
            pass
