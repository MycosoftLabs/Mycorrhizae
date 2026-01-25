"""
Mycorrhizae Channel Management

Channels are named message streams in the Mycorrhizae Protocol.
Supports device telemetry, agent communication, and computed streams.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import UUID

from .message import MycorrhizaeMessage


class ChannelType(str, Enum):
    """Types of channels in the Mycorrhizae Protocol."""
    DEVICE = "device"         # Device telemetry streams
    AGGREGATE = "aggregate"   # Aggregated/computed data
    COMPUTED = "computed"     # ML/AI computed insights
    ALERT = "alert"           # Alert/event channels
    COMMAND = "command"       # Device command channels
    AGENT = "agent"           # MAS agent communication
    SYSTEM = "system"         # Internal system channels


@dataclass
class Channel:
    """
    A named message channel in the Mycorrhizae Protocol.
    
    Channel naming convention:
    - device.<serial>.telemetry - Device sensor data
    - device.<serial>.alerts - Device alerts
    - agent.<agent_id>.tasks - Agent task queue
    - aggregate.fungi.observations - Aggregated observations
    - system.health - System health checks
    """
    
    name: str
    channel_type: ChannelType = ChannelType.DEVICE
    description: str = ""
    
    # Access control
    required_scopes: List[str] = field(default_factory=lambda: ["read"])
    write_scopes: List[str] = field(default_factory=lambda: ["write"])
    
    # Channel stats
    message_count: int = 0
    subscriber_count: int = 0
    last_message_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Configuration
    persist_messages: bool = True  # Store in MINDEX
    max_message_size: int = 1024 * 1024  # 1MB default
    ttl_seconds: int = 3600  # Default message TTL
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def matches_pattern(self, pattern: str) -> bool:
        """Check if channel name matches a pattern with wildcards."""
        # Convert glob pattern to regex
        regex = pattern.replace(".", r"\.").replace("*", r"[^.]+").replace("#", r".*")
        return bool(re.match(f"^{regex}$", self.name))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert channel to dictionary."""
        return {
            "name": self.name,
            "type": self.channel_type.value,
            "description": self.description,
            "required_scopes": self.required_scopes,
            "write_scopes": self.write_scopes,
            "message_count": self.message_count,
            "subscriber_count": self.subscriber_count,
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
            "created_at": self.created_at.isoformat(),
            "persist_messages": self.persist_messages,
            "ttl_seconds": self.ttl_seconds,
            "tags": self.tags,
        }


# Type for subscription callbacks
SubscriptionCallback = Callable[[MycorrhizaeMessage], None]


@dataclass
class Subscription:
    """A subscription to a channel."""
    id: UUID
    channel_pattern: str  # Can include wildcards: device.*.telemetry
    callback: SubscriptionCallback
    api_key_id: Optional[UUID] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    message_count: int = 0
    active: bool = True


class ChannelManager:
    """
    Manages channels and subscriptions for the Mycorrhizae Protocol.
    
    Supports:
    - Channel registration with access control
    - Pattern-based subscriptions (device.*.telemetry)
    - Message routing to subscribers
    - Channel statistics
    """
    
    # Standard channel prefixes
    DEVICE_PREFIX = "device"
    AGENT_PREFIX = "agent"
    AGGREGATE_PREFIX = "aggregate"
    SYSTEM_PREFIX = "system"
    ALERT_PREFIX = "alert"
    
    def __init__(self):
        self._channels: Dict[str, Channel] = {}
        self._subscriptions: Dict[str, List[Subscription]] = {}  # channel -> subscriptions
        self._pattern_subscriptions: List[Subscription] = []  # Pattern-based
    
    def register_channel(
        self,
        name: str,
        channel_type: ChannelType = ChannelType.DEVICE,
        description: str = "",
        required_scopes: Optional[List[str]] = None,
        write_scopes: Optional[List[str]] = None,
        persist_messages: bool = True,
        ttl_seconds: int = 3600,
        tags: Optional[List[str]] = None,
    ) -> Channel:
        """Register a new channel."""
        if name in self._channels:
            return self._channels[name]
        
        channel = Channel(
            name=name,
            channel_type=channel_type,
            description=description,
            required_scopes=required_scopes or ["read"],
            write_scopes=write_scopes or ["write"],
            persist_messages=persist_messages,
            ttl_seconds=ttl_seconds,
            tags=tags or [],
        )
        
        self._channels[name] = channel
        self._subscriptions[name] = []
        
        return channel
    
    def get_channel(self, name: str) -> Optional[Channel]:
        """Get a channel by name."""
        return self._channels.get(name)
    
    def list_channels(
        self,
        channel_type: Optional[ChannelType] = None,
        prefix: Optional[str] = None,
    ) -> List[Channel]:
        """List channels with optional filters."""
        channels = list(self._channels.values())
        
        if channel_type:
            channels = [c for c in channels if c.channel_type == channel_type]
        
        if prefix:
            channels = [c for c in channels if c.name.startswith(prefix)]
        
        return channels
    
    def subscribe(
        self,
        channel_pattern: str,
        callback: SubscriptionCallback,
        api_key_id: Optional[UUID] = None,
    ) -> Subscription:
        """
        Subscribe to a channel or pattern.
        
        Patterns can include wildcards:
        - device.*.telemetry - All device telemetry
        - device.mycelium-001.* - All channels for specific device
        - # - All channels (use sparingly)
        """
        from uuid import uuid4
        
        subscription = Subscription(
            id=uuid4(),
            channel_pattern=channel_pattern,
            callback=callback,
            api_key_id=api_key_id,
        )
        
        # Check if pattern contains wildcards
        if "*" in channel_pattern or "#" in channel_pattern:
            self._pattern_subscriptions.append(subscription)
        else:
            # Direct channel subscription
            if channel_pattern not in self._subscriptions:
                self._subscriptions[channel_pattern] = []
            self._subscriptions[channel_pattern].append(subscription)
            
            # Update subscriber count
            if channel_pattern in self._channels:
                self._channels[channel_pattern].subscriber_count += 1
        
        return subscription
    
    def unsubscribe(self, subscription_id: UUID) -> bool:
        """Remove a subscription."""
        # Check pattern subscriptions
        for i, sub in enumerate(self._pattern_subscriptions):
            if sub.id == subscription_id:
                self._pattern_subscriptions.pop(i)
                return True
        
        # Check direct subscriptions
        for channel_name, subs in self._subscriptions.items():
            for i, sub in enumerate(subs):
                if sub.id == subscription_id:
                    subs.pop(i)
                    if channel_name in self._channels:
                        self._channels[channel_name].subscriber_count -= 1
                    return True
        
        return False
    
    def get_subscribers(self, channel_name: str) -> List[Subscription]:
        """Get all active subscribers for a channel."""
        subscribers = []
        
        # Direct subscribers
        if channel_name in self._subscriptions:
            subscribers.extend([s for s in self._subscriptions[channel_name] if s.active])
        
        # Pattern subscribers
        for sub in self._pattern_subscriptions:
            if sub.active:
                # Check if channel matches pattern
                channel = Channel(name=channel_name)
                if channel.matches_pattern(sub.channel_pattern):
                    subscribers.append(sub)
        
        return subscribers
    
    def publish(self, message: MycorrhizaeMessage) -> int:
        """
        Publish a message to subscribers.
        
        Returns the number of subscribers notified.
        """
        if not message.channel:
            return 0
        
        # Update channel stats
        if message.channel in self._channels:
            channel = self._channels[message.channel]
            channel.message_count += 1
            channel.last_message_at = datetime.now(timezone.utc)
        
        # Get subscribers
        subscribers = self.get_subscribers(message.channel)
        notified = 0
        
        for sub in subscribers:
            try:
                sub.callback(message)
                sub.message_count += 1
                notified += 1
            except Exception as e:
                # Log error but continue
                print(f"Error notifying subscriber {sub.id}: {e}")
        
        return notified
    
    def register_standard_channels(self) -> None:
        """Register standard system channels."""
        # System channels
        self.register_channel(
            "system.health",
            ChannelType.SYSTEM,
            "System health heartbeats",
            required_scopes=["read"],
            write_scopes=["admin"],
        )
        self.register_channel(
            "system.events",
            ChannelType.SYSTEM,
            "System-wide events",
            required_scopes=["read"],
            write_scopes=["admin"],
        )
        
        # Alert channels
        self.register_channel(
            "alert.critical",
            ChannelType.ALERT,
            "Critical alerts requiring immediate attention",
            required_scopes=["read", "alert:critical"],
            write_scopes=["write", "alert:emit"],
        )
        self.register_channel(
            "alert.warning",
            ChannelType.ALERT,
            "Warning level alerts",
            required_scopes=["read"],
            write_scopes=["write"],
        )
        
        # Aggregate channels
        self.register_channel(
            "aggregate.fungi.observations",
            ChannelType.AGGREGATE,
            "Aggregated fungal observations from all sources",
            required_scopes=["read"],
            write_scopes=["etl:run"],
        )
        self.register_channel(
            "aggregate.sensors.telemetry",
            ChannelType.AGGREGATE,
            "Aggregated sensor telemetry",
            required_scopes=["read"],
            write_scopes=["device:write"],
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get channel manager statistics."""
        total_messages = sum(c.message_count for c in self._channels.values())
        total_subscribers = sum(c.subscriber_count for c in self._channels.values())
        total_subscribers += len(self._pattern_subscriptions)
        
        return {
            "channel_count": len(self._channels),
            "subscriber_count": total_subscribers,
            "total_messages": total_messages,
            "pattern_subscriptions": len(self._pattern_subscriptions),
            "channels_by_type": {
                ct.value: len([c for c in self._channels.values() if c.channel_type == ct])
                for ct in ChannelType
            }
        }
