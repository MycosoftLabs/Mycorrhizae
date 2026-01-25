"""
Mycorrhizae Protocol Message Format

Defines the standardized message structure for all data flowing through
the Mycorrhizae Protocol - from devices to MINDEX to agents.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


class MessageType(str, Enum):
    """Types of messages in the Mycorrhizae Protocol."""
    TELEMETRY = "telemetry"      # Sensor readings, device data
    EVENT = "event"              # Discrete events, alerts
    COMMAND = "command"          # Control commands to devices
    INSIGHT = "insight"          # AI-generated insights
    QUERY = "query"              # Database queries
    RESPONSE = "response"        # Query responses
    HEARTBEAT = "heartbeat"      # Keep-alive messages


class SourceType(str, Enum):
    """Source types that can publish to Mycorrhizae."""
    FCI = "fci"                  # Fungal Computer Interface
    DEVICE = "device"            # MycoBrain device
    SENSOR = "sensor"            # Individual sensor
    MAS_AGENT = "mas_agent"      # MYCA MAS agent
    MINDEX = "mindex"            # MINDEX database
    ETL = "etl"                  # ETL pipeline
    DASHBOARD = "dashboard"      # User dashboard
    API = "api"                  # External API
    SYSTEM = "system"            # Internal system


@dataclass
class MycorrhizaeMessage:
    """
    A message in the Mycorrhizae Protocol.
    
    This is the core data structure that flows through all channels,
    from device telemetry to AI insights. All messages are:
    - Timestamped with UTC datetime
    - Uniquely identified with UUIDs
    - Traceable via correlation IDs
    - Authenticated via API key references
    """
    
    # Identity
    id: UUID = field(default_factory=uuid4)
    channel: str = ""
    
    # Timing
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ttl_seconds: int = 3600  # Default 1 hour TTL
    
    # Source identification
    source_type: SourceType = SourceType.DEVICE
    source_id: Optional[str] = None
    device_serial: Optional[str] = None
    
    # Message content
    message_type: MessageType = MessageType.TELEMETRY
    payload: Dict[str, Any] = field(default_factory=dict)
    
    # Tracing and auth
    correlation_id: Optional[UUID] = None
    reply_to: Optional[str] = None
    api_key_id: Optional[UUID] = None  # For audit trail
    
    # Metadata
    priority: int = 5  # 1-10, higher is more important
    tags: list = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        return {
            "id": str(self.id),
            "channel": self.channel,
            "timestamp": self.timestamp.isoformat(),
            "ttl_seconds": self.ttl_seconds,
            "source": {
                "type": self.source_type.value if isinstance(self.source_type, SourceType) else self.source_type,
                "id": self.source_id,
                "device_serial": self.device_serial,
            },
            "message_type": self.message_type.value if isinstance(self.message_type, MessageType) else self.message_type,
            "payload": self.payload,
            "tracing": {
                "correlation_id": str(self.correlation_id) if self.correlation_id else None,
                "reply_to": self.reply_to,
                "api_key_id": str(self.api_key_id) if self.api_key_id else None,
            },
            "priority": self.priority,
            "tags": self.tags,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())
    
    def to_ndjson(self) -> str:
        """Serialize to compact NDJSON format."""
        return json.dumps(self.to_dict(), separators=(",", ":"))
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MycorrhizaeMessage":
        """Create message from dictionary."""
        source = data.get("source", {})
        tracing = data.get("tracing", {})
        
        return cls(
            id=UUID(data["id"]) if "id" in data else uuid4(),
            channel=data.get("channel", ""),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(timezone.utc),
            ttl_seconds=data.get("ttl_seconds", 3600),
            source_type=SourceType(source.get("type", "device")),
            source_id=source.get("id"),
            device_serial=source.get("device_serial"),
            message_type=MessageType(data.get("message_type", "telemetry")),
            payload=data.get("payload", {}),
            correlation_id=UUID(tracing["correlation_id"]) if tracing.get("correlation_id") else None,
            reply_to=tracing.get("reply_to"),
            api_key_id=UUID(tracing["api_key_id"]) if tracing.get("api_key_id") else None,
            priority=data.get("priority", 5),
            tags=data.get("tags", []),
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> "MycorrhizaeMessage":
        """Create message from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def is_expired(self) -> bool:
        """Check if message TTL has expired."""
        age = (datetime.now(timezone.utc) - self.timestamp).total_seconds()
        return age > self.ttl_seconds
    
    def create_reply(self, payload: Dict[str, Any], message_type: MessageType = MessageType.RESPONSE) -> "MycorrhizaeMessage":
        """Create a reply message linked to this one."""
        return MycorrhizaeMessage(
            channel=self.reply_to or self.channel,
            message_type=message_type,
            payload=payload,
            correlation_id=self.correlation_id or self.id,
            source_type=SourceType.SYSTEM,
        )


# Type alias for callback functions
MessageCallback = callable  # Callable[[MycorrhizaeMessage], None]
