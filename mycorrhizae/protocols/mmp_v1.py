"""
MMP v1 Protocol Implementation

Mycosoft Mycorrhizae Protocol v1 - binary protocol with SHA-256
truncated hash and enhanced 32-byte header.
Uses COBS framing (same as MDP).
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, Optional, Tuple

from .mdp_framing import COBSCodec
from .mmp_crypto import compute_mmp_trailer, verify_mmp_trailer
from .mmp_types import (
    MMPDeviceType,
    MMPFlags,
    MMPPayloadType,
    MMPv1Frame,
    MMPv1Header,
    MMPv1Trailer,
    MMP_HEADER_SIZE,
    MMP_TRAILER_SIZE,
)

logger = logging.getLogger(__name__)


class MMPv1Encoder:
    """Encoder for MMP v1 messages."""

    def __init__(
        self,
        device_id: int = 0,
        device_type: int = MMPDeviceType.MYCOBRAIN,
    ):
        self.device_id = device_id
        self.device_type = device_type
        self.seq = 0
        self.cobs = COBSCodec()

    def _next_seq(self) -> int:
        s = self.seq
        self.seq = (self.seq + 1) & 0xFFFFFFFF
        return s

    def encode_frame(
        self,
        payload_type: MMPPayloadType,
        payload: bytes,
        flags: int = 0,
    ) -> bytes:
        """Encode raw payload to COBS-encoded MMP frame."""
        header = MMPv1Header(
            device_type=self.device_type,
            device_id=self.device_id,
            timestamp=int(time.time() * 1000),
            seq=self._next_seq(),
            payload_type=payload_type,
            flags=flags,
            payload_len=len(payload),
        )
        header_payload = header.to_bytes() + payload
        hash8, crc8_val = compute_mmp_trailer(header_payload)
        trailer = MMPv1Trailer(hash8=hash8, crc8=crc8_val)
        raw = header_payload + trailer.to_bytes()
        return self.cobs.encode(raw)

    def encode_telemetry(self, telemetry: Dict[str, Any]) -> bytes:
        """Encode telemetry payload."""
        payload = json.dumps(telemetry).encode("utf-8")
        return self.encode_frame(MMPPayloadType.TELEMETRY, payload)

    def encode_command(self, command: Dict[str, Any]) -> bytes:
        """Encode command payload with ACK requested."""
        payload = json.dumps(command).encode("utf-8")
        return self.encode_frame(
            MMPPayloadType.COMMAND,
            payload,
            flags=int(MMPFlags.ACK_REQUESTED),
        )

    def encode_ack(self, ack_seq: int, success: bool = True) -> bytes:
        """Encode ACK message."""
        payload = json.dumps({"ack_seq": ack_seq, "success": success}).encode("utf-8")
        flags = int(MMPFlags.IS_ACK) if success else int(MMPFlags.IS_NACK)
        return self.encode_frame(MMPPayloadType.ACK, payload, flags=flags)


class MMPv1Decoder:
    """Decoder for MMP v1 messages."""

    def __init__(self, validate_trailer: bool = True):
        self.cobs = COBSCodec()
        self.validate_trailer = validate_trailer

    def decode(self, data: bytes) -> Tuple[MMPv1Frame, Dict[str, Any]]:
        """
        Decode a single COBS-encoded MMP frame.
        Returns (frame, payload_dict).
        """
        raw = self.cobs.decode(data)
        return self._decode_one(raw)

    def _decode_one(self, raw: bytes) -> Tuple[MMPv1Frame, Dict[str, Any]]:
        """Decode raw bytes (after COBS) to frame and payload dict."""
        if len(raw) < MMP_HEADER_SIZE + MMP_TRAILER_SIZE:
            raise ValueError(
                f"Frame too short: {len(raw)} < {MMP_HEADER_SIZE + MMP_TRAILER_SIZE}"
            )
        header = MMPv1Header.from_bytes(raw)
        if not header.validate():
            raise ValueError(f"Invalid MMP header: magic=0x{header.magic:04x} ver={header.version}")

        payload = raw[MMP_HEADER_SIZE : MMP_HEADER_SIZE + header.payload_len]
        trailer_data = raw[-(MMP_TRAILER_SIZE) :]
        trailer = MMPv1Trailer.from_bytes(trailer_data)
        header_payload = raw[: MMP_HEADER_SIZE + header.payload_len]

        if self.validate_trailer:
            if not verify_mmp_trailer(header_payload, trailer.hash8, trailer.crc8):
                raise ValueError("MMP trailer integrity check failed")

        frame = MMPv1Frame(header=header, payload=payload, trailer=trailer)
        payload_str = payload.decode("utf-8")
        payload_dict = json.loads(payload_str)
        return frame, payload_dict
