"""
Tests for Mycorrhizae channel management and pattern matching.
"""

import pytest

from mycorrhizae.channels import Channel, ChannelType


class TestChannel:
    """Channel model and pattern matching tests."""

    def test_channel_matches_exact(self):
        ch = Channel(name="device.SIDE_A.telemetry", channel_type=ChannelType.DEVICE)
        assert ch.matches_pattern("device.SIDE_A.telemetry")

    def test_channel_matches_wildcard_star(self):
        ch = Channel(name="device.MCB001.telemetry", channel_type=ChannelType.DEVICE)
        assert ch.matches_pattern("device.*.telemetry")

    def test_channel_does_not_match_wrong_pattern(self):
        ch = Channel(name="device.MCB001.telemetry", channel_type=ChannelType.DEVICE)
        assert not ch.matches_pattern("device.MCB001.command")

    def test_channel_to_dict(self):
        ch = Channel(
            name="test.channel",
            channel_type=ChannelType.AGGREGATE,
            description="Test",
        )
        d = ch.to_dict()
        assert d["name"] == "test.channel"
        assert d["type"] == "aggregate"
        assert "description" in d
