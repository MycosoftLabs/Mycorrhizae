"""
Redis Message Broker Integration

Provides distributed pub/sub and streams for the Mycorrhizae Protocol
using Redis as the message broker.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import UUID

import redis.asyncio as aioredis

from .message import MycorrhizaeMessage
from .channels import Channel, ChannelManager


class RedisBroker:
    """
    Redis-backed message broker for Mycorrhizae Protocol.
    
    Features:
    - Pub/Sub for real-time message distribution
    - Streams for persistent message queues
    - Consumer groups for MAS agent load balancing
    - Automatic reconnection handling
    """
    
    CHANNEL_PREFIX = "mycorrhizae:"
    STREAM_PREFIX = "mycorrhizae:stream:"
    DEDUPE_PREFIX = "mycorrhizae:dedupe:"
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        channel_manager: Optional[ChannelManager] = None,
    ):
        self.redis_url = redis_url
        self.channel_manager = channel_manager or ChannelManager()
        
        self._redis: Optional[aioredis.Redis] = None
        self._pubsub: Optional[aioredis.client.PubSub] = None
        self._subscriptions: Dict[str, Set[Callable]] = {}
        self._running = False
        self._listener_task: Optional[asyncio.Task] = None
    
    async def connect(self) -> None:
        """Connect to Redis."""
        self._redis = await aioredis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        self._pubsub = self._redis.pubsub()
        print(f"[RedisBroker] Connected to {self.redis_url}")
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        self._running = False
        
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        
        if self._pubsub:
            await self._pubsub.close()
        
        if self._redis:
            await self._redis.close()
        
        print("[RedisBroker] Disconnected")
    
    async def publish(self, message: MycorrhizaeMessage) -> int:
        """
        Publish a message to Redis.
        
        Publishes to:
        1. Pub/Sub channel for real-time subscribers
        2. Stream for persistent storage (if configured)
        
        Returns number of subscribers that received the message.
        """
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        # Dedupe device telemetry by (deviceId, seq, msgId) when present.
        try:
            env = message.payload if isinstance(message.payload, dict) else {}
            hdr = env.get("hdr") if isinstance(env, dict) else None
            if isinstance(hdr, dict) and "deviceId" in hdr and "msgId" in hdr and "seq" in env:
                device_id = str(hdr.get("deviceId"))
                msg_id = str(hdr.get("msgId"))
                seq = env.get("seq")
                if isinstance(seq, int):
                    dedupe_key = f"{self.DEDUPE_PREFIX}{device_id}:{seq}:{msg_id}"
                    was_set = await self._redis.set(dedupe_key, "1", ex=message.ttl_seconds, nx=True)
                    if not was_set:
                        return 0
        except Exception:
            # Dedupe must never crash publishing.
            pass

        redis_channel = f"{self.CHANNEL_PREFIX}{message.channel}"
        message_json = message.to_json()
        
        # Publish to pub/sub
        subscribers = await self._redis.publish(redis_channel, message_json)
        
        # Add to stream for persistence
        channel = self.channel_manager.get_channel(message.channel)
        if channel and channel.persist_messages:
            stream_key = f"{self.STREAM_PREFIX}{message.channel}"
            await self._redis.xadd(
                stream_key,
                {
                    "id": str(message.id),
                    "data": message_json,
                    "timestamp": str(int(message.timestamp.timestamp() * 1000)),
                },
                maxlen=10000,  # Keep last 10k messages
            )
        
        return subscribers
    
    async def subscribe(
        self,
        channel_pattern: str,
        callback: Callable[[MycorrhizaeMessage], None],
    ) -> str:
        """
        Subscribe to a channel pattern.
        
        Uses Redis pattern subscriptions for wildcard support.
        """
        if not self._pubsub:
            raise RuntimeError("Not connected to Redis")
        
        redis_pattern = f"{self.CHANNEL_PREFIX}{channel_pattern}"
        
        # Track subscription
        if redis_pattern not in self._subscriptions:
            self._subscriptions[redis_pattern] = set()
            
            # Subscribe to Redis pattern
            if "*" in redis_pattern or "?" in redis_pattern:
                await self._pubsub.psubscribe(redis_pattern)
            else:
                await self._pubsub.subscribe(redis_pattern)
        
        self._subscriptions[redis_pattern].add(callback)
        
        # Start listener if not running
        if not self._running:
            self._running = True
            self._listener_task = asyncio.create_task(self._listen())
        
        return redis_pattern
    
    async def unsubscribe(
        self,
        channel_pattern: str,
        callback: Callable[[MycorrhizaeMessage], None],
    ) -> bool:
        """Remove a subscription callback."""
        redis_pattern = f"{self.CHANNEL_PREFIX}{channel_pattern}"
        
        if redis_pattern not in self._subscriptions:
            return False
        
        self._subscriptions[redis_pattern].discard(callback)
        
        # Unsubscribe from Redis if no more callbacks
        if not self._subscriptions[redis_pattern]:
            del self._subscriptions[redis_pattern]
            
            if self._pubsub:
                if "*" in redis_pattern or "?" in redis_pattern:
                    await self._pubsub.punsubscribe(redis_pattern)
                else:
                    await self._pubsub.unsubscribe(redis_pattern)
        
        return True
    
    async def _listen(self) -> None:
        """Listen for messages from Redis pub/sub."""
        if not self._pubsub:
            return
        
        try:
            async for msg in self._pubsub.listen():
                if not self._running:
                    break
                
                if msg["type"] in ("message", "pmessage"):
                    # Extract channel and data
                    channel = msg.get("channel", msg.get("pattern", ""))
                    data = msg.get("data", "")
                    
                    if not data or not isinstance(data, str):
                        continue
                    
                    try:
                        message = MycorrhizaeMessage.from_json(data)
                    except Exception as e:
                        print(f"[RedisBroker] Failed to parse message: {e}")
                        continue
                    
                    # Find matching subscriptions
                    for pattern, callbacks in self._subscriptions.items():
                        if self._matches_pattern(channel, pattern):
                            for callback in callbacks:
                                try:
                                    callback(message)
                                except Exception as e:
                                    print(f"[RedisBroker] Callback error: {e}")
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[RedisBroker] Listener error: {e}")
    
    def _matches_pattern(self, channel: str, pattern: str) -> bool:
        """Check if channel matches subscription pattern."""
        if "*" not in pattern and "?" not in pattern:
            return channel == pattern
        
        # Simple glob matching
        import fnmatch
        return fnmatch.fnmatch(channel, pattern)
    
    # ==================== Stream Operations ====================
    
    async def read_stream(
        self,
        channel: str,
        count: int = 100,
        from_id: str = "-",
    ) -> List[MycorrhizaeMessage]:
        """Read messages from a stream."""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        stream_key = f"{self.STREAM_PREFIX}{channel}"
        
        entries = await self._redis.xrange(stream_key, from_id, "+", count=count)
        
        messages = []
        for entry_id, data in entries:
            try:
                msg = MycorrhizaeMessage.from_json(data.get("data", "{}"))
                messages.append(msg)
            except Exception:
                continue
        
        return messages
    
    async def create_consumer_group(
        self,
        channel: str,
        group_name: str,
        start_id: str = "$",
    ) -> bool:
        """Create a consumer group for a stream."""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        stream_key = f"{self.STREAM_PREFIX}{channel}"
        
        try:
            await self._redis.xgroup_create(stream_key, group_name, start_id, mkstream=True)
            return True
        except Exception as e:
            if "BUSYGROUP" in str(e):
                return True  # Group already exists
            raise
    
    async def read_group(
        self,
        channel: str,
        group_name: str,
        consumer_name: str,
        count: int = 10,
        block_ms: int = 5000,
    ) -> List[MycorrhizaeMessage]:
        """Read messages from a stream as part of a consumer group."""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        stream_key = f"{self.STREAM_PREFIX}{channel}"
        
        entries = await self._redis.xreadgroup(
            group_name,
            consumer_name,
            {stream_key: ">"},
            count=count,
            block=block_ms,
        )
        
        messages = []
        for stream, stream_entries in entries:
            for entry_id, data in stream_entries:
                try:
                    msg = MycorrhizaeMessage.from_json(data.get("data", "{}"))
                    messages.append(msg)
                except Exception:
                    continue
        
        return messages
    
    async def acknowledge(
        self,
        channel: str,
        group_name: str,
        message_ids: List[str],
    ) -> int:
        """Acknowledge messages in a consumer group."""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        stream_key = f"{self.STREAM_PREFIX}{channel}"
        return await self._redis.xack(stream_key, group_name, *message_ids)
    
    # ==================== Stats ====================
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get broker statistics."""
        if not self._redis:
            return {"connected": False}
        
        info = await self._redis.info()
        
        return {
            "connected": True,
            "redis_version": info.get("redis_version"),
            "connected_clients": info.get("connected_clients"),
            "used_memory_human": info.get("used_memory_human"),
            "total_commands_processed": info.get("total_commands_processed"),
            "pubsub_channels": info.get("pubsub_channels"),
            "pubsub_patterns": info.get("pubsub_patterns"),
            "subscription_count": len(self._subscriptions),
        }
