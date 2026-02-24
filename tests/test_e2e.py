"""
End-to-end flow tests - MDP encode -> Gateway -> Message.
"""

import pytest

from mycorrhizae.gateway.device_gateway import DeviceGateway
from mycorrhizae.protocols.mdp_v1 import MDPv1Encoder, MDPv1Decoder
from mycorrhizae.protocols.mdp_types import MDPEndpoint
from mycorrhizae.protocols.mmp_v1 import MMPv1Encoder, MMPv1Decoder
from mycorrhizae.protocols.mmp_types import MMPDeviceType


class TestE2EFlows:
    """End-to-end protocol flow tests."""

    def test_mdp_telemetry_full_flow(self):
        """MDP: encode telemetry -> decode -> gateway -> message."""
        enc = MDPv1Encoder(src=MDPEndpoint.SIDE_A, dst=MDPEndpoint.GATEWAY)
        dec = MDPv1Decoder()
        gw = DeviceGateway(broker=None)

        telemetry = {"ai1": 1.5, "ai2": 2.5, "temp": 23.0}
        encoded = enc.encode_telemetry(telemetry)
        assert len(encoded) > 0

        frame, payload = dec.decode(encoded)
        assert payload == telemetry

        msg = gw.handle_frame(encoded)
        assert msg is not None
        assert msg.payload["pack"] == telemetry
        assert msg.payload["protocol"] == "mdp_v1"

    def test_mmp_telemetry_full_flow(self):
        """MMP: encode telemetry -> decode -> gateway -> message."""
        enc = MMPv1Encoder(device_id=1, device_type=MMPDeviceType.MYCOBRAIN)
        dec = MMPv1Decoder()
        gw = DeviceGateway(broker=None)

        telemetry = {"v": 3.14}
        encoded = enc.encode_telemetry(telemetry)
        frame, payload = dec.decode(encoded)
        assert payload == telemetry

        msg = gw.handle_frame(encoded)
        assert msg is not None
        assert msg.payload["pack"] == telemetry
        assert msg.payload["protocol"] == "mmp_v1"

    def test_gateway_encode_command_roundtrip(self):
        """Gateway encode_command produces decodable MDP frame."""
        gw = DeviceGateway(broker=None)
        dec = MDPv1Decoder()

        cmd = {"cmd": "read_sensors", "params": {"interval": 5}}
        encoded = gw.encode_command("SIDE_A", cmd)
        frame, payload = dec.decode(encoded)
        assert payload["cmd"] == "read_sensors"
        assert payload.get("params", {}).get("interval") == 5
