"""
MDP v1 Protocol Implementation

Full encoder/decoder for Mycosoft Device Protocol v1.
Uses COBS framing and CRC-16 for error detection.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Tuple

from .mdp_types import (
    MDPEndpoint,
    MDPv1Frame,
    MDPv1Header,
    MDPMessageType,
    MDPTelemetryPayload,
    MDPCommandPayload,
)
from .mdp_framing import COBSCodec, CRC16Calculator

logger = logging.getLogger(__name__)


class MDPv1Encoder:
    """Encoder for MDP v1 messages."""

    def __init__(
        self,
        src: int = MDPEndpoint.GATEWAY,
        dst: int = MDPEndpoint.SIDE_A,
    ):
        self.src = src
        self.dst = dst
        self.seq = 0
        self.cobs = COBSCodec()
        self.crc = CRC16Calculator()

    def _next_seq(self) -> int:
        s = self.seq
        self.seq = (self.seq + 1) & 0xFFFFFFFF
        return s

    def encode_frame(
        self,
        msg_type: MDPMessageType,
        payload: bytes,
        ack: int = 0,
        flags: int = 0,
    ) -> bytes:
        """Encode raw payload to COBS-encoded frame."""
        header = MDPv1Header(
            msg_type=msg_type,
            seq=self._next_seq(),
            ack=ack,
            flags=flags,
            src=self.src,
            dst=self.dst,
        )
        frame = MDPv1Frame(header=header, payload=payload)
        raw = frame.to_bytes(self.crc)
        return self.cobs.encode(raw)

    def encode_telemetry(self, telemetry: Dict[str, Any]) -> bytes:
        """Encode telemetry payload."""
        payload = json.dumps(telemetry).encode("utf-8")
        return self.encode_frame(MDPMessageType.TELEMETRY, payload)

    def encode_command(self, command: Dict[str, Any]) -> bytes:
        """Encode command payload."""
        payload = json.dumps(command).encode("utf-8")
        return self.encode_frame(
            MDPMessageType.COMMAND,
            payload,
            flags=0x01,  # ACK_REQUESTED
        )

    def encode_ack(self, ack_seq: int, success: bool = True) -> bytes:
        """Encode ACK message."""
        payload = json.dumps({
            "success": success,
            "ack_sequence": ack_seq,
        }).encode("utf-8")
        return self.encode_frame(
            MDPMessageType.ACK,
            payload,
            ack=ack_seq,
            flags=0x02,  # IS_ACK
        )


class MDPv1Decoder:
    """Decoder for MDP v1 messages."""

    def __init__(self, validate_crc: bool = True):
        self.validate_crc = validate_crc
        self.cobs = COBSCodec()
        self.crc = CRC16Calculator()
        self._buffer = bytearray()
        self._received_seqs: set[int] = set()
        self._max_tracked = 1000

    def feed(self, data: bytes) -> list[Tuple[MDPv1Frame, Dict[str, Any]]]:
        """
        Feed raw bytes and return list of (frame, parsed_payload) for complete frames.
        """
        self._buffer.extend(data)
        frames_raw, remainder = self.cobs.extract_frames(bytes(self._buffer))
        self._buffer = bytearray(remainder)

        results = []
        for raw in frames_raw:
            try:
                frame, payload = self._decode_one(raw)
                results.append((frame, payload))
            except (ValueError, json.JSONDecodeError) as e:
                logger.warning("MDP decode error: %s", e)
        return results

    def _decode_one(self, raw: bytes) -> Tuple[MDPv1Frame, Dict[str, Any]]:
        """Decode a single raw frame (after COBS decode)."""
        frame = MDPv1Frame.from_bytes(raw, self.crc, validate_crc=self.validate_crc)
        if not frame.header.validate():
            raise ValueError(f"Invalid header: magic=0x{frame.header.magic:04x}")

        if frame.header.seq in self._received_seqs:
            logger.debug("Duplicate sequence %d", frame.header.seq)
        else:
            self._received_seqs.add(frame.header.seq)
            if len(self._received_seqs) > self._max_tracked:
                self._received_seqs = set(list(self._received_seqs)[-self._max_tracked:])

        payload_str = frame.payload.decode("utf-8")
        payload_dict = json.loads(payload_str)
        return frame, payload_dict

    def decode(self, data: bytes) -> Tuple[MDPv1Frame, Dict[str, Any]]:
        """
        Decode a single COBS-encoded frame. For use when exact frame boundaries known.
        """
        decoded = self.cobs.decode(data)
        return self._decode_one(decoded)
