"""
Tests for DeviceGateway - MDP/MMP frame to Mycorrhizae message conversion.
"""

import pytest

from mycorrhizae.gateway.device_gateway import DeviceGateway
from mycorrhizae.protocols.mdp_v1 import MDPv1Encoder
from mycorrhizae.protocols.mdp_types import MDPEndpoint, MDPMessageType
from mycorrhizae.protocols.mmp_v1 import MMPv1Encoder
from mycorrhizae.protocols.mmp_types import MMPDeviceType


class TestDeviceGateway:
    """DeviceGateway unit tests."""

    def test_handle_mdp_telemetry_frame(self, device_gateway):
        enc = MDPv1Encoder(src=MDPEndpoint.SIDE_A, dst=MDPEndpoint.GATEWAY)
        encoded = enc.encode_telemetry({"ai1": 1.2, "temp": 22.0})
        msg = device_gateway.handle_mdp_frame(encoded)
        assert msg is not None
        assert "device" in msg.channel
        assert "telemetry" in msg.channel
        assert msg.payload.get("protocol") == "mdp_v1"
        assert msg.payload.get("pack", {}).get("ai1") == 1.2

    def test_handle_mdp_command_frame(self, device_gateway):
        enc = MDPv1Encoder(src=MDPEndpoint.SIDE_A, dst=MDPEndpoint.GATEWAY)
        encoded = enc.encode_command({"cmd": "read_sensors"})
        msg = device_gateway.handle_mdp_frame(encoded)
        assert msg is not None
        assert "command" in msg.channel

    def test_handle_mmp_telemetry_frame(self, device_gateway):
        enc = MMPv1Encoder(device_id=0x42, device_type=MMPDeviceType.MYCOBRAIN)
        encoded = enc.encode_telemetry({"v": 3.14})
        msg = device_gateway.handle_mmp_frame(encoded)
        assert msg is not None
        assert "device" in msg.channel
        assert "MMP_" in msg.channel and "42" in msg.channel
        assert msg.payload.get("protocol") == "mmp_v1"

    def test_handle_frame_auto_detects_mdp(self, device_gateway):
        enc = MDPv1Encoder(src=MDPEndpoint.SIDE_A, dst=MDPEndpoint.GATEWAY)
        encoded = enc.encode_telemetry({"x": 1})
        msg = device_gateway.handle_frame(encoded)
        assert msg is not None
        assert msg.payload.get("protocol") == "mdp_v1"

    def test_handle_frame_auto_detects_mmp(self, device_gateway):
        enc = MMPv1Encoder(device_id=1, device_type=MMPDeviceType.MYCOBRAIN)
        encoded = enc.encode_telemetry({"x": 1})
        msg = device_gateway.handle_frame(encoded)
        assert msg is not None
        assert msg.payload.get("protocol") == "mmp_v1"

    def test_encode_command(self, device_gateway):
        cmd = {"cmd": "read_sensors", "params": {}}
        encoded = device_gateway.encode_command("SIDE_A", cmd)
        assert isinstance(encoded, bytes)
        assert len(encoded) > 0
