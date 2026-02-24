"""
Tests for MDP v1 protocol - COBS framing, CRC-16, encode/decode.
"""

import pytest

from mycorrhizae.protocols.mdp_framing import COBSCodec, CRC16Calculator
from mycorrhizae.protocols.mdp_types import (
    MDPEndpoint,
    MDPv1Frame,
    MDPv1Header,
    MDPMessageType,
    MDP_HEADER_SIZE,
)
from mycorrhizae.protocols.mdp_v1 import MDPv1Decoder, MDPv1Encoder


class TestCRC16Calculator:
    """CRC16-CCITT-FALSE tests."""

    def test_empty_data(self):
        calc = CRC16Calculator()
        assert calc.calculate(b"") == 0xFFFF

    def test_simple_data(self):
        calc = CRC16Calculator()
        crc = calc.calculate(b"123456789")
        assert isinstance(crc, int)
        assert 0 <= crc <= 0xFFFF

    def test_deterministic(self):
        calc = CRC16Calculator()
        data = b"telemetry payload"
        assert calc.calculate(data) == calc.calculate(data)


class TestCOBSCodec:
    """COBS encode/decode tests."""

    def test_encode_decode_roundtrip(self):
        codec = COBSCodec()
        data = b"hello"
        encoded = codec.encode(data)
        assert 0x00 in encoded
        decoded = codec.decode(encoded)
        assert decoded == data

    def test_encode_no_internal_zeros_simple(self):
        codec = COBSCodec()
        data = b"abc"
        encoded = codec.encode(data)
        inner = encoded[1:-1]
        assert 0x00 not in inner

    def test_encode_empty(self):
        codec = COBSCodec()
        encoded = codec.encode(b"")
        assert encoded[-1] == 0x00
        decoded = codec.decode(encoded)
        assert decoded == b""

    def test_encode_with_zero_byte(self):
        codec = COBSCodec()
        data = bytes([0x01, 0x00, 0x02])
        encoded = codec.encode(data)
        decoded = codec.decode(encoded)
        assert decoded == data

    def test_extract_frames(self):
        codec = COBSCodec()
        f1 = codec.encode(b"frame1")
        f2 = codec.encode(b"frame2")
        buffer = f1 + f2
        frames, remainder = codec.extract_frames(buffer)
        assert len(frames) == 2
        assert frames[0] == b"frame1"
        assert frames[1] == b"frame2"
        assert remainder == b""

    def test_extract_frames_with_remainder(self):
        codec = COBSCodec()
        f1 = codec.encode(b"frame1")
        # Incomplete COBS frame (no trailing 0x00) - should be remainder
        partial = b"\x02\x66"
        buffer = f1 + partial
        frames, remainder = codec.extract_frames(buffer)
        assert len(frames) == 1
        assert frames[0] == b"frame1"
        assert remainder == partial


class TestMDPv1Header:
    """MDP v1 header tests."""

    def test_roundtrip(self):
        h = MDPv1Header(
            msg_type=MDPMessageType.TELEMETRY,
            seq=42,
            src=MDPEndpoint.SIDE_A,
            dst=MDPEndpoint.GATEWAY,
        )
        raw = h.to_bytes()
        assert len(raw) == MDP_HEADER_SIZE
        h2 = MDPv1Header.from_bytes(raw)
        assert h2.magic == h.magic
        assert h2.seq == h.seq
        assert h2.src == h.src
        assert h2.dst == h.dst

    def test_validate(self):
        h = MDPv1Header()
        assert h.validate()


class TestMDPv1EncoderDecoder:
    """MDP v1 full encode/decode tests."""

    def test_telemetry_roundtrip(self, mdp_encoder, mdp_decoder):
        telemetry = {"ai1": 1.2, "ai2": 2.3, "temp": 22.5}
        encoded = mdp_encoder.encode_telemetry(telemetry)
        assert isinstance(encoded, bytes)
        assert len(encoded) > 0

        frame, payload = mdp_decoder.decode(encoded)
        assert frame.header.msg_type == MDPMessageType.TELEMETRY
        assert payload["ai1"] == 1.2
        assert payload["temp"] == 22.5

    def test_command_roundtrip(self, mdp_encoder, mdp_decoder):
        cmd = {"cmd": "read_sensors", "params": {}}
        encoded = mdp_encoder.encode_command(cmd)
        frame, payload = mdp_decoder.decode(encoded)
        assert frame.header.msg_type == MDPMessageType.COMMAND
        assert payload["cmd"] == "read_sensors"

    def test_ack_roundtrip(self, mdp_encoder, mdp_decoder):
        encoded = mdp_encoder.encode_ack(ack_seq=10, success=True)
        frame, payload = mdp_decoder.decode(encoded)
        assert frame.header.msg_type == MDPMessageType.ACK
        assert payload["success"] is True
        assert payload["ack_sequence"] == 10

    def test_feed_multiple_frames(self, mdp_encoder, mdp_decoder):
        enc1 = mdp_encoder.encode_telemetry({"v": 1})
        enc2 = mdp_encoder.encode_telemetry({"v": 2})
        buffer = enc1 + enc2
        results = mdp_decoder.feed(buffer)
        assert len(results) == 2
        assert results[0][1]["v"] == 1
        assert results[1][1]["v"] == 2
