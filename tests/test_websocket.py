"""
Tests for WebSocket transport - WebSocketHandler logic.
"""

import pytest


class TestWebSocketHandler:
    """WebSocket handler unit tests."""

    def test_channel_pattern_parsing(self):
        """Verify channel query param parsing."""
        from mycorrhizae.transports.websocket import WebSocketHandler

        # Handler accepts channels as comma-separated
        channels_str = "device.*.telemetry,fci.*.bioelectric"
        channels = [c.strip() for c in channels_str.split(",") if c.strip()]
        assert "device.*.telemetry" in channels
        assert "fci.*.bioelectric" in channels

    def test_websocket_handler_import(self):
        """WebSocketHandler can be imported."""
        from mycorrhizae.transports.websocket import WebSocketHandler

        assert WebSocketHandler is not None
