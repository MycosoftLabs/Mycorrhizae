"""
SSE Streaming Endpoints

Server-Sent Events for real-time channel subscriptions.
"""

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sse_starlette.sse import EventSourceResponse

from mycorrhizae import MycorrhizaeProtocol, MycorrhizaeMessage
from services.key_service import KeyServiceManager, APIKey
from pydantic import BaseModel, Field


router = APIRouter()


# ==================== Dependencies ====================

async def get_protocol_dep() -> MycorrhizaeProtocol:
    """Get protocol instance."""
    from api.main import get_protocol
    return await get_protocol()


async def get_key_service_dep() -> KeyServiceManager:
    """Get key service instance."""
    from api.main import get_key_service
    return await get_key_service()


async def validate_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
    key_svc: KeyServiceManager = Depends(get_key_service_dep),
) -> APIKey:
    """Validate the API key from header."""
    result = await key_svc.validate_key(
        raw_key=x_api_key,
        required_scopes=["read", "channel:subscribe"],
    )
    if not result.valid:
        raise HTTPException(status_code=403, detail=result.error)
    return result.key


# ==================== SSE Generator ====================

async def message_generator(
    channel_pattern: str,
    proto: MycorrhizaeProtocol,
    api_key_id: Optional[str] = None,
):
    """
    Async generator that yields SSE events for a channel pattern.
    """
    message_queue: asyncio.Queue = asyncio.Queue()
    
    def callback(msg: MycorrhizaeMessage):
        try:
            message_queue.put_nowait(msg)
        except asyncio.QueueFull:
            pass  # Drop message if queue is full
    
    # Subscribe to channel pattern
    from uuid import UUID
    subscription = proto.subscribe(
        channel_pattern=channel_pattern,
        callback=callback,
        api_key_id=UUID(api_key_id) if api_key_id else None,
    )
    
    try:
        # Send initial connection event
        yield {
            "event": "connected",
            "data": json.dumps({
                "subscription_id": str(subscription.id),
                "channel_pattern": channel_pattern,
            })
        }
        
        # Stream messages
        while True:
            try:
                # Wait for message with timeout (for keepalive)
                msg = await asyncio.wait_for(message_queue.get(), timeout=30.0)
                
                yield {
                    "event": "message",
                    "data": msg.to_json(),
                    "id": str(msg.id),
                }
                
            except asyncio.TimeoutError:
                # Send keepalive ping
                yield {
                    "event": "ping",
                    "data": json.dumps({"ts": asyncio.get_event_loop().time()}),
                }
                
    finally:
        # Cleanup subscription
        proto.unsubscribe(subscription.id)


# ==================== Endpoints ====================

@router.get("/subscribe")
async def subscribe_to_channel(
    channel: str = Query(..., description="Channel pattern (supports wildcards)"),
    x_api_key: str = Header(..., alias="X-API-Key"),
    key_svc: KeyServiceManager = Depends(get_key_service_dep),
    proto: MycorrhizaeProtocol = Depends(get_protocol_dep),
):
    """
    Subscribe to a channel via Server-Sent Events.
    
    The channel parameter supports wildcards:
    - device.*.telemetry - All device telemetry
    - device.mycelium-001.* - All channels for a device
    - system.* - All system channels
    
    The connection will:
    1. Validate your API key
    2. Send a 'connected' event with subscription details
    3. Stream 'message' events as they arrive
    4. Send 'ping' events every 30 seconds as keepalive
    """
    # Validate API key
    result = await key_svc.validate_key(
        raw_key=x_api_key,
        required_scopes=["read", "channel:subscribe"],
    )
    if not result.valid:
        raise HTTPException(status_code=403, detail=result.error)
    
    return EventSourceResponse(
        message_generator(
            channel_pattern=channel,
            proto=proto,
            api_key_id=str(result.key.id) if result.key else None,
        )
    )


@router.get("/channels")
async def list_subscribable_channels(
    api_key: APIKey = Depends(validate_api_key),
    proto: MycorrhizaeProtocol = Depends(get_protocol_dep),
):
    """List channels available for subscription."""
    channels = proto.list_channels()
    
    # Filter by scopes
    accessible = []
    for c in channels:
        # Check if user has required scopes
        if "admin" in api_key.scopes:
            accessible.append(c.name)
        elif any(scope in api_key.scopes for scope in c.required_scopes):
            accessible.append(c.name)
        elif "read" in api_key.scopes and "read" in c.required_scopes:
            accessible.append(c.name)
    
    return {
        "channels": accessible,
        "count": len(accessible),
        "patterns": [
            "device.*.telemetry",
            "device.*.alerts",
            "agent.*.tasks",
            "aggregate.*",
            "system.*",
        ],
    }


class ReplayAckRequest(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=200)
    msg_id: str = Field(..., min_length=1, max_length=200)
    seq: int = Field(..., ge=0)
    accepted: bool = True
    reason: Optional[str] = None


@router.post("/replay/ack")
async def ack_replay_message(
    request: ReplayAckRequest,
    x_api_key: str = Header(..., alias="X-API-Key"),
    key_svc: KeyServiceManager = Depends(get_key_service_dep),
    proto: MycorrhizaeProtocol = Depends(get_protocol_dep),
):
    """
    Record a replay ACK and publish it on a per-device ack channel.

    This is used by gateways/ingestors to let edge devices advance their durable
    replay tail safely (exactly-once semantics by contract).
    """
    result = await key_svc.validate_key(raw_key=x_api_key, required_scopes=["write", "device:write"])
    if not result.valid:
        raise HTTPException(status_code=403, detail=result.error)

    from mycorrhizae.envelope_contract import build_replay_ack
    ack = build_replay_ack(
        device_id=request.device_id,
        msg_id=request.msg_id,
        seq=request.seq,
        accepted=request.accepted,
        reason=request.reason,
    )

    # Publish ACK into the protocol fabric (can be streamed to gateways/devices).
    msg = MycorrhizaeMessage(
        channel=f"device.{request.device_id}.ack",
        message_type="event",
        source_type="system",
        source_id="mycorrhizae",
        payload=ack,
        tags=["ack"],
        ttl_seconds=3600,
    )
    await proto.publish(msg, api_key=x_api_key)

    return ack
