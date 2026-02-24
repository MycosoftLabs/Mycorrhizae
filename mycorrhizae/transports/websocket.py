"""
WebSocket transport for Mycorrhizae Protocol.

Bidirectional real-time streaming over WebSocket.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable, Optional, Set

from ..message import MycorrhizaeMessage

logger = logging.getLogger(__name__)


class WebSocketHandler:
    """
    Handles WebSocket connection for channel subscriptions.
    Subscribes to channel patterns and forwards messages to the WebSocket.
    """

    def __init__(
        self,
        websocket,
        protocol,
        channel_patterns: list[str],
        api_key_id: Optional[str] = None,
    ):
        self.websocket = websocket
        self.protocol = protocol
        self.channel_patterns = list(channel_patterns) if channel_patterns else ["*"]
        self.api_key_id = api_key_id
        self._subscriptions: list = []
        self._running = False
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._recv_task: Optional[asyncio.Task] = None

    def _make_callback(self) -> Callable[[MycorrhizaeMessage], None]:
        def callback(msg: MycorrhizaeMessage):
            try:
                self._queue.put_nowait(msg)
            except asyncio.QueueFull:
                logger.warning("WebSocket message queue full, dropping message")

        return callback

    async def _subscribe(self) -> None:
        from uuid import UUID

        for pattern in self.channel_patterns:
            sub = self.protocol.subscribe(
                channel_pattern=pattern,
                callback=self._make_callback(),
                api_key_id=UUID(self.api_key_id) if self.api_key_id else None,
            )
            self._subscriptions.append(sub)

    def _unsubscribe_all(self) -> None:
        for sub in self._subscriptions:
            try:
                self.protocol.unsubscribe(sub.id)
            except Exception:
                pass
        self._subscriptions.clear()

    async def send_message(self, msg: MycorrhizaeMessage) -> None:
        """Send a message to the WebSocket client."""
        try:
            await self.websocket.send_json({
                "event": "message",
                "data": msg.to_dict(),
                "id": str(msg.id),
            })
        except Exception as e:
            logger.warning("WebSocket send error: %s", e)

    async def run(self) -> None:
        """Run the WebSocket handler - subscribe and forward messages."""
        self._running = True
        await self._subscribe()

        try:
            await self.websocket.send_json({
                "event": "connected",
                "data": {
                    "channel_patterns": self.channel_patterns,
                    "subscription_count": len(self._subscriptions),
                },
            })

            while self._running:
                try:
                    msg = await asyncio.wait_for(self._queue.get(), timeout=30.0)
                    await self.send_message(msg)
                except asyncio.TimeoutError:
                    await self.websocket.send_json({
                        "event": "ping",
                        "data": {"ts": asyncio.get_event_loop().time()},
                    })
        finally:
            self._running = False
            self._unsubscribe_all()
