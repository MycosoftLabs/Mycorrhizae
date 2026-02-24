"""
Async Mycorrhizae Protocol Client

Subscribe to channels via SSE or WebSocket and publish messages.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable, Dict, Optional

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

try:
    import websockets
    HAS_WS = True
except ImportError:
    HAS_WS = False


class MycorrhizaeAsyncClient:
    """
    Async client for the Mycorrhizae Protocol API.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8002",
        api_key: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or ""

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["X-API-Key"] = self.api_key
        return h

    async def publish(
        self,
        channel: str,
        payload: Dict[str, Any],
        message_type: str = "telemetry",
    ) -> bool:
        """Publish a message to a channel via the API."""
        if not HAS_HTTPX:
            raise ImportError("httpx required: pip install httpx")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.base_url}/api/channels/{channel}/publish",
                    json={
                        "payload": payload,
                        "message_type": message_type,
                    },
                    headers=self._headers(),
                )
            return resp.status_code in (200, 201)
        except Exception:
            return False

    async def subscribe_sse(
        self,
        channel_pattern: str,
        callback: Callable[[Dict[str, Any]], None],
    ) -> None:
        """Subscribe to channel via SSE (Server-Sent Events)."""
        if not HAS_HTTPX:
            raise ImportError("httpx required: pip install httpx")
        url = f"{self.base_url}/api/stream/subscribe?channel={channel_pattern}"
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("GET", url, headers=self._headers()) as resp:
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            callback(data)
                        except json.JSONDecodeError:
                            pass

    async def subscribe_websocket(
        self,
        callback: Callable[[Dict[str, Any]], None],
        channel_patterns: str = "device.*.telemetry",
    ) -> None:
        """Subscribe to channels via WebSocket."""
        if not HAS_WS:
            raise ImportError("websockets required: pip install websockets")
        ws_url = self.base_url.replace("http", "ws")
        url = f"{ws_url}/api/ws/subscribe?channels={channel_patterns}"
        async with websockets.connect(url) as ws:
            if self.api_key:
                await ws.send(json.dumps({"type": "auth", "api_key": self.api_key}))
            async for msg in ws:
                try:
                    data = json.loads(msg)
                    if data.get("event") == "message" and "data" in data:
                        callback(data["data"])
                except json.JSONDecodeError:
                    pass
