"""
Channel Management Endpoints

CRUD operations for Mycorrhizae Protocol channels.
"""

import os
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field

from mycorrhizae import MycorrhizaeProtocol, ChannelType
from services.key_service import KeyServiceManager, APIKey


router = APIRouter()


# ==================== Pydantic Models ====================

class ChannelResponse(BaseModel):
    """Channel information."""
    name: str
    type: str
    description: str
    required_scopes: List[str]
    write_scopes: List[str]
    message_count: int
    subscriber_count: int
    last_message_at: Optional[str]
    created_at: str
    persist_messages: bool
    ttl_seconds: int
    tags: List[str]


class CreateChannelRequest(BaseModel):
    """Request to create a channel."""
    name: str = Field(..., min_length=1, max_length=200)
    type: str = Field(default="device")
    description: str = Field(default="")
    required_scopes: List[str] = Field(default=["read"])
    write_scopes: List[str] = Field(default=["write"])
    persist_messages: bool = Field(default=True)
    ttl_seconds: int = Field(default=3600, ge=60, le=86400 * 30)
    tags: List[str] = Field(default=[])


class PublishRequest(BaseModel):
    """Request to publish a message."""
    payload: dict
    message_type: str = Field(default="telemetry")
    source_id: Optional[str] = None
    device_serial: Optional[str] = None
    priority: int = Field(default=5, ge=1, le=10)
    tags: List[str] = Field(default=[])


class PublishResponse(BaseModel):
    """Response from publishing a message."""
    message_id: str
    channel: str
    subscribers_notified: int
    persisted: bool


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
    result = await key_svc.validate_key(raw_key=x_api_key)
    if not result.valid:
        raise HTTPException(status_code=403, detail=result.error)
    return result.key


# ==================== Endpoints ====================

@router.get("", response_model=List[ChannelResponse])
async def list_channels(
    type: Optional[str] = None,
    prefix: Optional[str] = None,
    api_key: APIKey = Depends(validate_api_key),
    proto: MycorrhizaeProtocol = Depends(get_protocol_dep),
):
    """List all channels."""
    channel_type = ChannelType(type) if type else None
    channels = proto.list_channels(channel_type=channel_type, prefix=prefix)
    
    return [
        ChannelResponse(
            name=c.name,
            type=c.channel_type.value,
            description=c.description,
            required_scopes=c.required_scopes,
            write_scopes=c.write_scopes,
            message_count=c.message_count,
            subscriber_count=c.subscriber_count,
            last_message_at=c.last_message_at.isoformat() if c.last_message_at else None,
            created_at=c.created_at.isoformat(),
            persist_messages=c.persist_messages,
            ttl_seconds=c.ttl_seconds,
            tags=c.tags,
        )
        for c in channels
    ]


@router.post("", response_model=ChannelResponse)
async def create_channel(
    request: CreateChannelRequest,
    api_key: APIKey = Depends(validate_api_key),
    proto: MycorrhizaeProtocol = Depends(get_protocol_dep),
):
    """Create a new channel."""
    # Check admin scope for channel creation
    if "admin" not in api_key.scopes and "channel:create" not in api_key.scopes:
        raise HTTPException(status_code=403, detail="Missing scope: channel:create")
    
    try:
        channel_type = ChannelType(request.type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid channel type: {request.type}")
    
    c = proto.register_channel(
        name=request.name,
        channel_type=channel_type,
        description=request.description,
        required_scopes=request.required_scopes,
        write_scopes=request.write_scopes,
        persist_messages=request.persist_messages,
        ttl_seconds=request.ttl_seconds,
        tags=request.tags,
    )
    
    return ChannelResponse(
        name=c.name,
        type=c.channel_type.value,
        description=c.description,
        required_scopes=c.required_scopes,
        write_scopes=c.write_scopes,
        message_count=c.message_count,
        subscriber_count=c.subscriber_count,
        last_message_at=c.last_message_at.isoformat() if c.last_message_at else None,
        created_at=c.created_at.isoformat(),
        persist_messages=c.persist_messages,
        ttl_seconds=c.ttl_seconds,
        tags=c.tags,
    )


@router.get("/{channel_name:path}", response_model=ChannelResponse)
async def get_channel(
    channel_name: str,
    api_key: APIKey = Depends(validate_api_key),
    proto: MycorrhizaeProtocol = Depends(get_protocol_dep),
):
    """Get a specific channel."""
    c = proto.get_channel(channel_name)
    if not c:
        raise HTTPException(status_code=404, detail=f"Channel not found: {channel_name}")
    
    return ChannelResponse(
        name=c.name,
        type=c.channel_type.value,
        description=c.description,
        required_scopes=c.required_scopes,
        write_scopes=c.write_scopes,
        message_count=c.message_count,
        subscriber_count=c.subscriber_count,
        last_message_at=c.last_message_at.isoformat() if c.last_message_at else None,
        created_at=c.created_at.isoformat(),
        persist_messages=c.persist_messages,
        ttl_seconds=c.ttl_seconds,
        tags=c.tags,
    )


@router.post("/{channel_name:path}/publish", response_model=PublishResponse)
async def publish_message(
    channel_name: str,
    request: PublishRequest,
    x_api_key: str = Header(..., alias="X-API-Key"),
    key_svc: KeyServiceManager = Depends(get_key_service_dep),
    proto: MycorrhizaeProtocol = Depends(get_protocol_dep),
):
    """Publish a message to a channel."""
    from mycorrhizae import MycorrhizaeMessage, MessageType, SourceType
    
    try:
        message_type = MessageType(request.message_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid message type: {request.message_type}")
    
    message = MycorrhizaeMessage(
        channel=channel_name,
        message_type=message_type,
        payload=request.payload,
        source_id=request.source_id,
        device_serial=request.device_serial,
        priority=request.priority,
        tags=request.tags,
    )

    # Optional envelope verification (local-first); can be enforced via env var.
    if isinstance(request.payload, dict) and "hdr" in request.payload and "hash" in request.payload and "sig" in request.payload:
        from mycorrhizae.envelope_contract import (
            validate_envelope_structure,
            verify_envelope_hash,
            verify_ed25519_signature,
        )

        require_sig = os.getenv("MYCORRHIZAE_REQUIRE_DEVICE_SIGNATURE", "false").strip().lower() == "true"

        v = validate_envelope_structure(request.payload)
        if not v.valid:
            raise HTTPException(status_code=400, detail=f"envelope_invalid:{v.reason}")

        hash_ok, hash_reason = verify_envelope_hash(request.payload)
        if not hash_ok:
            raise HTTPException(status_code=400, detail=f"envelope_hash_invalid:{hash_reason}")

        # Signature verify is optional unless enforced.
        device_pk_b64 = await key_svc.get_device_public_key_b64(v.device_id or "")
        sig_ok = False
        sig_reason = "no_device_key"
        if device_pk_b64:
            # Recompute payload hash bytes based on declared algorithm.
            from mycorrhizae.envelope_contract import _parse_hash  # type: ignore

            payload_hash = _parse_hash(request.payload.get("hash"))
            if payload_hash:
                sig_ok, sig_reason = verify_ed25519_signature(
                    str(request.payload.get("sig")),
                    payload_hash,
                    device_pk_b64,
                )
            else:
                sig_ok, sig_reason = False, "invalid_hash_field"

        if require_sig and not sig_ok:
            raise HTTPException(status_code=403, detail=f"envelope_signature_invalid:{sig_reason}")

        request.payload.setdefault("verification", {})
        request.payload["verification"].update(
            {
                "hashValid": True,
                "signatureValid": sig_ok,
                "signatureReason": sig_reason,
            }
        )
    
    try:
        notified = await proto.publish(message, api_key=x_api_key)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    channel = proto.get_channel(channel_name)
    
    return PublishResponse(
        message_id=str(message.id),
        channel=channel_name,
        subscribers_notified=notified,
        persisted=channel.persist_messages if channel else False,
    )
