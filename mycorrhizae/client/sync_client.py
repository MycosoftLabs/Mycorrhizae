"""
Sync Mycorrhizae Protocol Client

Thin wrapper around async client for synchronous use.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from .async_client import MycorrhizaeAsyncClient


class MycorrhizaeClient:
    """
    Synchronous client - runs async operations in a new event loop.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8002",
        api_key: Optional[str] = None,
    ):
        self._async_client = MycorrhizaeAsyncClient(base_url=base_url, api_key=api_key)

    def publish(
        self,
        channel: str,
        payload: Dict[str, Any],
        message_type: str = "telemetry",
    ) -> bool:
        """Publish a message to a channel."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self._async_client.publish(channel, payload, message_type)
        )

    def subscribe(
        self,
        channel_pattern: str,
        callback: Callable[[Dict[str, Any]], None],
        transport: str = "sse",
    ) -> None:
        """Subscribe to channel (blocks)."""
        import asyncio
        if transport == "websocket":
            asyncio.get_event_loop().run_until_complete(
                self._async_client.subscribe_websocket(channel_pattern, callback)
            )
        else:
            asyncio.get_event_loop().run_until_complete(
                self._async_client.subscribe_sse(channel_pattern, callback)
            )
