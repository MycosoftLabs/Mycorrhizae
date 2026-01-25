"""
Mycorrhizae Protocol - Main Protocol Implementation

The central router for all biological sensor data in the Mycosoft ecosystem.
Handles message routing, API key validation, and persistence.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID

from .message import MycorrhizaeMessage, MessageType, SourceType
from .channels import Channel, ChannelType, ChannelManager, Subscription, SubscriptionCallback


class MycorrhizaeProtocol:
    """
    The Mycorrhizae Protocol - Data Protocol for Nature.
    
    Routes biological sensor data between:
    - MycoBrain devices (FCI, BME688, M-Wave sensors)
    - MINDEX database (canonical data layer)
    - MYCA agents (multi-agent system)
    - NatureOS dashboards (user interfaces)
    - Ledger anchoring (blockchain immutability)
    
    Features:
    - Channel-based pub/sub messaging
    - API key authentication and rate limiting
    - Message persistence to MINDEX
    - Redis-backed real-time distribution
    - HPL (Hypha Programming Language) evaluation
    """
    
    VERSION = "1.0.0"
    
    def __init__(
        self,
        key_service=None,
        mindex_client=None,
        redis_client=None,
    ):
        """
        Initialize the Mycorrhizae Protocol.
        
        Args:
            key_service: KeyServiceManager for API key validation
            mindex_client: MINDEX database client for persistence
            redis_client: Redis client for distributed pub/sub
        """
        self.key_service = key_service
        self.mindex_client = mindex_client
        self.redis_client = redis_client
        
        self.channel_manager = ChannelManager()
        self.channel_manager.register_standard_channels()
        
        self._started = False
        self._message_handlers: List[Callable[[MycorrhizaeMessage], None]] = []
    
    async def start(self) -> None:
        """Start the protocol (connect to Redis, etc.)."""
        if self._started:
            return
        
        # Connect to Redis if configured
        if self.redis_client:
            await self._setup_redis_subscriptions()
        
        self._started = True
    
    async def stop(self) -> None:
        """Stop the protocol gracefully."""
        self._started = False
    
    async def _setup_redis_subscriptions(self) -> None:
        """Set up Redis pub/sub for distributed messaging."""
        pass  # Implemented in broker.py
    
    def register_channel(
        self,
        name: str,
        channel_type: ChannelType = ChannelType.DEVICE,
        description: str = "",
        required_scopes: Optional[List[str]] = None,
        write_scopes: Optional[List[str]] = None,
        **kwargs,
    ) -> Channel:
        """
        Register a new channel in the protocol.
        
        Args:
            name: Channel name (e.g., "device.mycelium-001.telemetry")
            channel_type: Type of channel
            description: Human-readable description
            required_scopes: Scopes needed to subscribe
            write_scopes: Scopes needed to publish
        
        Returns:
            The registered Channel object
        """
        return self.channel_manager.register_channel(
            name=name,
            channel_type=channel_type,
            description=description,
            required_scopes=required_scopes,
            write_scopes=write_scopes,
            **kwargs,
        )
    
    def subscribe(
        self,
        channel_pattern: str,
        callback: SubscriptionCallback,
        api_key_id: Optional[UUID] = None,
    ) -> Subscription:
        """
        Subscribe to a channel or pattern.
        
        Patterns support wildcards:
        - device.*.telemetry - All device telemetry
        - device.mycelium-001.* - All channels for a device
        
        Args:
            channel_pattern: Channel name or pattern
            callback: Function to call with each message
            api_key_id: Optional API key for audit
        
        Returns:
            Subscription object
        """
        return self.channel_manager.subscribe(
            channel_pattern=channel_pattern,
            callback=callback,
            api_key_id=api_key_id,
        )
    
    def unsubscribe(self, subscription_id: UUID) -> bool:
        """Remove a subscription."""
        return self.channel_manager.unsubscribe(subscription_id)
    
    async def publish(
        self,
        message: MycorrhizaeMessage,
        api_key: Optional[str] = None,
    ) -> int:
        """
        Publish a message to the protocol.
        
        Args:
            message: The message to publish
            api_key: Optional API key for authentication
        
        Returns:
            Number of subscribers notified
        """
        # Validate API key if provided
        if api_key and self.key_service:
            result = await self.key_service.validate_key(
                raw_key=api_key,
                required_scopes=["write", "channel:publish"],
            )
            if not result.valid:
                raise PermissionError(f"API key validation failed: {result.error}")
            message.api_key_id = result.key.id
        
        # Ensure channel exists
        channel = self.channel_manager.get_channel(message.channel)
        if not channel:
            # Auto-register device channels
            if message.channel.startswith("device."):
                channel = self.register_channel(
                    name=message.channel,
                    channel_type=ChannelType.DEVICE,
                    description=f"Auto-registered device channel",
                )
            else:
                raise ValueError(f"Channel not found: {message.channel}")
        
        # Persist to MINDEX if configured
        if channel.persist_messages and self.mindex_client:
            await self._persist_message(message)
        
        # Publish to Redis for distribution
        if self.redis_client:
            await self._publish_redis(message)
        
        # Notify local subscribers
        notified = self.channel_manager.publish(message)
        
        # Call registered handlers
        for handler in self._message_handlers:
            try:
                handler(message)
            except Exception as e:
                print(f"Handler error: {e}")
        
        return notified
    
    async def _persist_message(self, message: MycorrhizaeMessage) -> None:
        """Persist message to MINDEX database."""
        if not self.mindex_client:
            return
        
        # Store in messages table
        await self.mindex_client.execute(
            """
            INSERT INTO mycorrhizae_messages (
                id, channel, timestamp, source_type, source_id,
                device_serial, message_type, payload, api_key_id,
                correlation_id, ttl_seconds
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """,
            message.id,
            message.channel,
            message.timestamp,
            message.source_type.value if hasattr(message.source_type, 'value') else message.source_type,
            message.source_id,
            message.device_serial,
            message.message_type.value if hasattr(message.message_type, 'value') else message.message_type,
            message.payload,
            message.api_key_id,
            message.correlation_id,
            message.ttl_seconds,
        )
    
    async def _publish_redis(self, message: MycorrhizaeMessage) -> None:
        """Publish message to Redis for distributed subscribers."""
        if not self.redis_client:
            return
        
        channel_key = f"mycorrhizae:{message.channel}"
        await self.redis_client.publish(channel_key, message.to_json())
    
    def register_handler(self, handler: Callable[[MycorrhizaeMessage], None]) -> None:
        """Register a global message handler."""
        self._message_handlers.append(handler)
    
    def create_device_message(
        self,
        device_serial: str,
        channel_suffix: str,
        payload: Dict[str, Any],
        message_type: MessageType = MessageType.TELEMETRY,
    ) -> MycorrhizaeMessage:
        """
        Helper to create a device message with proper channel naming.
        
        Args:
            device_serial: Device serial number
            channel_suffix: Channel suffix (telemetry, alerts, commands)
            payload: Message payload
            message_type: Type of message
        
        Returns:
            Properly formatted MycorrhizaeMessage
        """
        return MycorrhizaeMessage(
            channel=f"device.{device_serial}.{channel_suffix}",
            source_type=SourceType.DEVICE,
            device_serial=device_serial,
            message_type=message_type,
            payload=payload,
        )
    
    def create_agent_message(
        self,
        agent_id: str,
        channel_suffix: str,
        payload: Dict[str, Any],
        message_type: MessageType = MessageType.TELEMETRY,
    ) -> MycorrhizaeMessage:
        """Helper to create an agent message."""
        return MycorrhizaeMessage(
            channel=f"agent.{agent_id}.{channel_suffix}",
            source_type=SourceType.MAS_AGENT,
            source_id=agent_id,
            message_type=message_type,
            payload=payload,
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get protocol statistics."""
        channel_stats = self.channel_manager.get_stats()
        return {
            "version": self.VERSION,
            "started": self._started,
            "handlers_registered": len(self._message_handlers),
            **channel_stats,
        }
    
    def get_channel(self, name: str) -> Optional[Channel]:
        """Get a channel by name."""
        return self.channel_manager.get_channel(name)
    
    def list_channels(self, **kwargs) -> List[Channel]:
        """List channels with optional filters."""
        return self.channel_manager.list_channels(**kwargs)


# Global protocol instance (singleton pattern)
_protocol_instance: Optional[MycorrhizaeProtocol] = None


def get_protocol() -> MycorrhizaeProtocol:
    """Get the global protocol instance."""
    global _protocol_instance
    if _protocol_instance is None:
        _protocol_instance = MycorrhizaeProtocol()
    return _protocol_instance


def set_protocol(protocol: MycorrhizaeProtocol) -> None:
    """Set the global protocol instance."""
    global _protocol_instance
    _protocol_instance = protocol
