"""
MDP v1 Protocol Type Definitions

Matches MycoBrain firmware mdp_hdr_v1_t structure.
Reference: mycobrain/firmware/common/mdp_types.h
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Dict, List, Optional

# Protocol constants (must match firmware)
MDP_MAGIC = 0xA15A
MDP_VER = 1

# Header size in bytes (matches mdp_hdr_v1_t)
MDP_HEADER_SIZE = 16


class MDPMessageType(IntEnum):
    """MDP v1 message types - matches firmware MdpMsgType."""
    TELEMETRY = 0x01
    COMMAND = 0x02
    ACK = 0x03
    EVENT = 0x05
    HELLO = 0x06
    WIFISENSE = 0x07
    DRONE_TELEMETRY = 0x08
    DRONE_MISSION_STATUS = 0x09


class MDPFlags(IntEnum):
    """MDP v1 flags - matches firmware MdpFlags."""
    ACK_REQUESTED = 0x01
    IS_ACK = 0x02
    IS_NACK = 0x04


class MDPEndpoint(IntEnum):
    """MDP endpoints - matches firmware EP_* defines."""
    SIDE_A = 0xA1
    SIDE_B = 0xB1
    GATEWAY = 0xC0
    BCAST = 0xFF


@dataclass
class MDPv1Header:
    """
    MDP v1 header - 16 bytes, matches mdp_hdr_v1_t.
    Layout: magic(2) version(1) msg_type(1) seq(4) ack(4) flags(1) src(1) dst(1) rsv(1)
    """
    magic: int = MDP_MAGIC
    version: int = MDP_VER
    msg_type: int = MDPMessageType.TELEMETRY
    seq: int = 0
    ack: int = 0
    flags: int = 0
    src: int = MDPEndpoint.SIDE_A
    dst: int = MDPEndpoint.GATEWAY
    rsv: int = 0

    STRUCT_FMT = "<HBBIIBBBB"  # magic(2) version(1) msg_type(1) seq(4) ack(4) flags(1) src(1) dst(1) rsv(1)

    def to_bytes(self) -> bytes:
        """Serialize header to 16 bytes."""
        return struct.pack(
            self.STRUCT_FMT,
            self.magic,
            self.version,
            self.msg_type,
            self.seq,
            self.ack,
            self.flags,
            self.src,
            self.dst,
            self.rsv,
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "MDPv1Header":
        """Parse header from bytes."""
        if len(data) < MDP_HEADER_SIZE:
            raise ValueError(f"Header too short: {len(data)} < {MDP_HEADER_SIZE}")
        unpacked = struct.unpack(cls.STRUCT_FMT, data[:MDP_HEADER_SIZE])
        return cls(
            magic=unpacked[0],
            version=unpacked[1],
            msg_type=unpacked[2],
            seq=unpacked[3],
            ack=unpacked[4],
            flags=unpacked[5],
            src=unpacked[6],
            dst=unpacked[7],
            rsv=unpacked[8],
        )

    def validate(self) -> bool:
        """Validate header magic and version."""
        return self.magic == MDP_MAGIC and self.version == MDP_VER


@dataclass
class MDPv1Frame:
    """Complete MDP v1 frame: header + payload + CRC16."""
    header: MDPv1Header
    payload: bytes
    crc16: int = 0

    def to_bytes(self, crc_calc: "CRC16Calculator") -> bytes:
        """Serialize frame to bytes (before COBS encoding)."""
        frame_data = self.header.to_bytes() + self.payload
        self.crc16 = crc_calc.calculate(frame_data)
        return frame_data + struct.pack("<H", self.crc16)

    @classmethod
    def from_bytes(
        cls,
        data: bytes,
        crc_calc: "CRC16Calculator",
        validate_crc: bool = True,
    ) -> MDPv1Frame:
        """Parse frame from bytes (after COBS decoding)."""
        if len(data) < MDP_HEADER_SIZE + 2:  # header + CRC16
            raise ValueError(f"Frame too short: {len(data)} bytes")
        frame_data = data[:-2]
        crc_received = struct.unpack("<H", data[-2:])[0]
        if validate_crc:
            crc_calculated = crc_calc.calculate(frame_data)
            if crc_received != crc_calculated:
                raise ValueError(
                    f"CRC16 mismatch: received 0x{crc_received:04x}, "
                    f"calculated 0x{crc_calculated:04x}"
                )
        header = MDPv1Header.from_bytes(frame_data)
        payload = frame_data[MDP_HEADER_SIZE:]
        return cls(header=header, payload=payload, crc16=crc_received)


# Payload type dataclasses for structured telemetry/commands
@dataclass
class MDPTelemetryPayload:
    """Telemetry payload from MycoBrain Side-A."""
    ai1_voltage: float = 0.0
    ai2_voltage: float = 0.0
    ai3_voltage: float = 0.0
    ai4_voltage: float = 0.0
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    pressure: Optional[float] = None
    gas_resistance: Optional[float] = None
    mosfet_states: List[bool] = field(default_factory=lambda: [False] * 4)
    i2c_addresses: List[int] = field(default_factory=list)
    power_status: Dict[str, Any] = field(default_factory=dict)
    firmware_version: Optional[str] = None
    uptime_seconds: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MDPTelemetryPayload":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class MDPCommandPayload:
    """Command payload to MycoBrain Side-A."""
    command_id: int
    command_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MDPCommandPayload":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
