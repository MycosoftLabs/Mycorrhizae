"""
Tests for MMP v1 protocol - SHA-256 hash, CRC-8, encode/decode.
"""

import pytest

from mycorrhizae.protocols.mmp_crypto import (
    crc8,
    sha256_truncated,
    compute_mmp_trailer,
    verify_mmp_trailer,
)
from mycorrhizae.protocols.mmp_types import (
    MMPDeviceType,
    MMPPayloadType,
    MMP_HEADER_SIZE,
    MMP_TRAILER_SIZE,
)
from mycorrhizae.protocols.mmp_v1 import MMPv1Decoder, MMPv1Encoder


class TestMMPCrypto:
    """MMP cryptographic support tests."""

    def test_crc8_deterministic(self):
        data = b"test payload"
        assert crc8(data) == crc8(data)

    def test_sha256_truncated_length(self):
        data = b"hello"
        h8 = sha256_truncated(data, 8)
        assert len(h8) == 8

    def test_compute_verify_trailer(self):
        data = b"header and payload"
        h8, c8 = compute_mmp_trailer(data)
        assert len(h8) == 8
        assert 0 <= c8 <= 255
        assert verify_mmp_trailer(data, h8, c8)

    def test_verify_fails_on_tampered_data(self):
        data = b"original"
        h8, c8 = compute_mmp_trailer(data)
        tampered = b"tampered"
        assert not verify_mmp_trailer(tampered, h8, c8)


class TestMMPv1EncoderDecoder:
    """MMP v1 full encode/decode tests."""

    def test_telemetry_roundtrip(self, mmp_encoder, mmp_decoder):
        telemetry = {"ai1": 1.0, "temp": 25.5}
        encoded = mmp_encoder.encode_telemetry(telemetry)
        assert isinstance(encoded, bytes)
        assert len(encoded) >= MMP_HEADER_SIZE + MMP_TRAILER_SIZE

        frame, payload = mmp_decoder.decode(encoded)
        assert frame.header.payload_type == MMPPayloadType.TELEMETRY
        assert frame.header.device_id == 0x1234
        assert payload["ai1"] == 1.0
        assert payload["temp"] == 25.5

    def test_command_roundtrip(self, mmp_encoder, mmp_decoder):
        cmd = {"cmd": "read_sensors"}
        encoded = mmp_encoder.encode_command(cmd)
        frame, payload = mmp_decoder.decode(encoded)
        assert frame.header.payload_type == MMPPayloadType.COMMAND
        assert payload["cmd"] == "read_sensors"

    def test_ack_roundtrip(self, mmp_encoder, mmp_decoder):
        encoded = mmp_encoder.encode_ack(ack_seq=5, success=True)
        frame, payload = mmp_decoder.decode(encoded)
        assert frame.header.payload_type == MMPPayloadType.ACK
        assert payload["ack_seq"] == 5
        assert payload["success"] is True

    def test_device_type_preserved(self, mmp_encoder, mmp_decoder):
        encoded = mmp_encoder.encode_telemetry({"x": 1})
        frame, _ = mmp_decoder.decode(encoded)
        assert frame.header.device_type == MMPDeviceType.MYCOBRAIN
