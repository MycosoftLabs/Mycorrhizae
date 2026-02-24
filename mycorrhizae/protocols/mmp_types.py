"""
MMP v1 Protocol Type Definitions

Mycosoft Mycorrhizae Protocol v1 - evolved from MDP with enhanced header
and cryptographic integrity (SHA-256 truncated hash).
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from enum import IntEnum

# MMP protocol constants
MMP_MAGIC = 0x4D4D  # "MM"
MMP_VER = 0x02
MMP_HEADER_SIZE = 32
MMP_TRAILER_SIZE = 9  # SHA256 truncated (8) + CRC8 (1)
MMP_HASH_SIZE = 8
MMP_CRC8_SIZE = 1


class MMPDeviceType(IntEnum):
    """Device type identifiers."""
    MYCOBRAIN = 0x01
    SPOREBASE = 0x02
    FCI = 0x03
    GATEWAY = 0x04
    UNKNOWN = 0xFF


class MMPPayloadType(IntEnum):
    """Payload type - compatible with MDP message types."""
    TELEMETRY = 0x01
    COMMAND = 0x02
    ACK = 0x03
    EVENT = 0x05
    HELLO = 0x06


class MMPFlags(IntEnum):
    """MMP flags."""
    ACK_REQUESTED = 0x01
    IS_ACK = 0x02
    IS_NACK = 0x04
    ENCRYPTED = 0x08
    PRIORITY_HIGH = 0x10


@dataclass
class MMPv1Header:
    """
    MMP v1 header - 32 bytes.
    Layout: magic(2) version(1) device_type(1) device_id(4) timestamp(8)
            seq(4) payload_type(1) flags(1) payload_len(2) reserved(8)
    """
    magic: int = MMP_MAGIC
    version: int = MMP_VER
    device_type: int = MMPDeviceType.MYCOBRAIN
    device_id: int = 0
    timestamp: int = 0
    seq: int = 0
    payload_type: int = MMPPayloadType.TELEMETRY
    flags: int = 0
    payload_len: int = 0
    reserved: bytes = b"\x00" * 8

    STRUCT_FMT = "<HBBIQIBBH8s"  # 2+1+1+4+8+4+1+1+2+8 = 32

    def to_bytes(self) -> bytes:
        """Serialize header to 32 bytes."""
        rsv = self.reserved
        if len(rsv) != 8:
            rsv = (rsv + b"\x00" * 8)[:8]
        return struct.pack(
            self.STRUCT_FMT,
            self.magic,
            self.version,
            self.device_type,
            self.device_id,
            self.timestamp,
            self.seq,
            self.payload_type,
            self.flags,
            self.payload_len,
            rsv,
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "MMPv1Header":
        """Parse header from bytes."""
        if len(data) < MMP_HEADER_SIZE:
            raise ValueError(f"Header too short: {len(data)} < {MMP_HEADER_SIZE}")
        unpacked = struct.unpack(cls.STRUCT_FMT, data[:MMP_HEADER_SIZE])
        return cls(
            magic=unpacked[0],
            version=unpacked[1],
            device_type=unpacked[2],
            device_id=unpacked[3],
            timestamp=unpacked[4],
            seq=unpacked[5],
            payload_type=unpacked[6],
            flags=unpacked[7],
            payload_len=unpacked[8],
            reserved=unpacked[9],
        )

    def validate(self) -> bool:
        """Validate header magic and version."""
        return self.magic == MMP_MAGIC and self.version == MMP_VER


@dataclass
class MMPv1Trailer:
    """MMP v1 trailer: SHA-256 truncated (8 bytes) + CRC-8 (1 byte)."""
    hash8: bytes  # 8 bytes
    crc8: int = 0

    def to_bytes(self) -> bytes:
        """Serialize trailer to 9 bytes."""
        return self.hash8[:8].ljust(8, b"\x00")[:8] + bytes([self.crc8 & 0xFF])

    @classmethod
    def from_bytes(cls, data: bytes) -> "MMPv1Trailer":
        """Parse trailer from last 9 bytes."""
        if len(data) < MMP_TRAILER_SIZE:
            raise ValueError(f"Trailer too short: {len(data)}")
        return cls(
            hash8=data[-MMP_TRAILER_SIZE:-1],
            crc8=data[-1],
        )


@dataclass
class MMPv1Frame:
    """Complete MMP v1 frame: header + payload + trailer."""
    header: MMPv1Header
    payload: bytes
    trailer: MMPv1Trailer
