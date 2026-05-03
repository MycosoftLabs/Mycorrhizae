"""
Device Gateway - bridges MDP/MMP frames to Mycorrhizae envelopes.

Converts device protocol frames to MycorrhizaeMessage and publishes
to Redis. Supports sending commands back to devices.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ..message import MessageType, MycorrhizaeMessage, SourceType
from ..protocols.mdp_v1 import MDPv1Decoder, MDPv1Encoder
from ..protocols.mdp_types import MDPEndpoint, MDPMessageType
from ..protocols.mmp_v1 import MMPv1Decoder, MMPv1Encoder

logger = logging.getLogger(__name__)


def _endpoint_to_serial(ep: int) -> str:
    """Map MDP endpoint to device serial string."""
    if ep == MDPEndpoint.SIDE_A:
        return "SIDE_A"
    if ep == MDPEndpoint.SIDE_B:
        return "SIDE_B"
    if ep == MDPEndpoint.GATEWAY:
        return "GATEWAY"
    return f"0x{ep:02x}"


def _serial_to_endpoint(serial: str) -> int:
    """Map device serial to MDP endpoint."""
    m = {"SIDE_A": MDPEndpoint.SIDE_A, "SIDE_B": MDPEndpoint.SIDE_B}
    return m.get(serial.upper(), MDPEndpoint.SIDE_A)


class DeviceGateway:
    """
    Gateway that converts MDP/MMP frames to Mycorrhizae messages
    and publishes to the broker.
    """

    def __init__(
        self,
        broker=None,
        prefer_mmp: bool = False,
    ):
        self.broker = broker
        self.prefer_mmp = prefer_mmp
        self._mdp_dec = MDPv1Decoder()
        self._mdp_enc = MDPv1Encoder(src=MDPEndpoint.GATEWAY, dst=MDPEndpoint.SIDE_A)
        self._mmp_dec = MMPv1Decoder()
        self._mmp_enc = MMPv1Encoder(device_type=0x01, device_id=0)

    def handle_mdp_frame(self, frame_bytes: bytes) -> Optional[MycorrhizaeMessage]:
        """
        Decode MDP frame and create MycorrhizaeMessage.
        Returns None if decode fails.
        """
        try:
            frame, payload = self._mdp_dec.decode(frame_bytes)
        except Exception as e:
            logger.warning("MDP decode failed: %s", e)
            return None

        serial = _endpoint_to_serial(frame.header.src)
        channel = f"device.{serial}.telemetry"
        if frame.header.msg_type == MDPMessageType.COMMAND:
            channel = f"device.{serial}.command"
        elif frame.header.msg_type == MDPMessageType.EVENT:
            channel = f"device.{serial}.event"
        elif frame.header.msg_type == MDPMessageType.ACK:
            channel = f"device.{serial}.ack"
        elif frame.header.msg_type == MDPMessageType.ACOUSTIC_RAW:
            channel = f"device.{serial}.maritime.acoustic_raw"
        elif frame.header.msg_type == MDPMessageType.ACOUSTIC_FINGERPRINT:
            channel = f"device.{serial}.maritime.acoustic_fingerprint"
        elif frame.header.msg_type == MDPMessageType.MAGNETIC_ANOMALY:
            channel = f"device.{serial}.maritime.magnetic_anomaly"
        elif frame.header.msg_type == MDPMessageType.OCEAN_ENVIRONMENT:
            channel = f"device.{serial}.maritime.ocean_environment"
        elif frame.header.msg_type == MDPMessageType.TACTICAL_ASSESSMENT:
            channel = f"device.{serial}.maritime.tactical_assessment"
        elif frame.header.msg_type == MDPMessageType.ZEETA_BRIDGE:
            channel = f"device.{serial}.maritime.zeeta_bridge"
        elif int(frame.header.msg_type) == 0x0B:
            channel = f"device.{serial}.emissions"

        msg = MycorrhizaeMessage(
            channel=channel,
            source_type=SourceType.DEVICE,
            source_id=serial,
            device_serial=serial,
            message_type=MessageType.TELEMETRY,
            payload={
                "hdr": {
                    "deviceId": serial,
                    "msgId": str(frame.header.seq),
                    "seq": frame.header.seq,
                },
                "ts": datetime.now(timezone.utc).isoformat(),
                "seq": frame.header.seq,
                "pack": payload,
                "protocol": "mdp_v1",
                "msg_type": int(frame.header.msg_type),
                "maritime": int(frame.header.msg_type) >= 0x20,
            },
            tags=["mdp", "device"],
        )
        return msg

    def handle_mmp_frame(self, frame_bytes: bytes) -> Optional[MycorrhizaeMessage]:
        """
        Decode MMP frame and create MycorrhizaeMessage.
        """
        try:
            frame, payload = self._mmp_dec.decode(frame_bytes)
        except Exception as e:
            logger.warning("MMP decode failed: %s", e)
            return None

        serial = f"MMP_{frame.header.device_id:08x}"
        channel = f"device.{serial}.telemetry"
        if frame.header.payload_type == 0x02:
            channel = f"device.{serial}.command"
        elif frame.header.payload_type == 0x03:
            channel = f"device.{serial}.ack"
        elif int(frame.header.payload_type) == 0x0B:
            channel = f"device.{serial}.emissions"

        msg = MycorrhizaeMessage(
            channel=channel,
            source_type=SourceType.DEVICE,
            source_id=serial,
            device_serial=serial,
            message_type=MessageType.TELEMETRY,
            payload={
                "hdr": {
                    "deviceId": serial,
                    "msgId": str(frame.header.seq),
                    "seq": frame.header.seq,
                },
                "ts": datetime.now(timezone.utc).isoformat(),
                "seq": frame.header.seq,
                "pack": payload,
                "protocol": "mmp_v1",
                "device_id": frame.header.device_id,
                "timestamp": frame.header.timestamp,
            },
            tags=["mmp", "device"],
        )
        return msg

    def handle_frame(self, frame_bytes: bytes) -> Optional[MycorrhizaeMessage]:
        """
        Auto-detect MDP vs MMP and decode.
        MMP uses magic 0x4D4D; MDP uses 0xA15A (after COBS decode).
        """
        try:
            from ..protocols.mdp_framing import COBSCodec

            raw = COBSCodec().decode(frame_bytes)
            if len(raw) >= 2:
                magic = raw[0] | (raw[1] << 8)
                if magic == 0x4D4D:
                    return self.handle_mmp_frame(frame_bytes)
        except Exception:
            pass
        return self.handle_mdp_frame(frame_bytes)

    async def publish_frame(self, frame_bytes: bytes) -> bool:
        """
        Decode frame and publish to broker.
        Returns True if published successfully.
        """
        msg = self.handle_frame(frame_bytes)
        if not msg or not self.broker:
            return False
        try:
            await self.broker.publish(msg)
            return True
        except Exception as e:
            logger.error("Publish failed: %s", e)
            return False

    def encode_command(self, device_id: str, command: Dict[str, Any]) -> bytes:
        """
        Encode command for device. Uses MDP by default.
        """
        return self._mdp_enc.encode_command(command)
