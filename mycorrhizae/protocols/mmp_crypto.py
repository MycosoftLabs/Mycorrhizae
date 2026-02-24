"""
MMP v1 Cryptographic Support

SHA-256 truncated hash (8 bytes) for integrity.
CRC-8 for quick error detection.
Optional Ed25519 for future signing (stub).
"""

from __future__ import annotations

import hashlib
import struct
from typing import Optional

# CRC-8 polynomial (common variant)
CRC8_POLY = 0x07
CRC8_INIT = 0x00


def crc8(data: bytes, init: int = CRC8_INIT) -> int:
    """Compute CRC-8 checksum."""
    crc = init
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ CRC8_POLY
            else:
                crc <<= 1
            crc &= 0xFF
    return crc


def sha256_truncated(data: bytes, length: int = 8) -> bytes:
    """
    Compute SHA-256 and truncate to `length` bytes (default 8).
    Uses first N bytes of the hash for integrity check.
    """
    h = hashlib.sha256(data).digest()
    return h[:length]


def compute_mmp_trailer(header_payload: bytes) -> tuple[bytes, int]:
    """
    Compute MMP trailer: (hash8, crc8).
    header_payload = header + payload (before trailer).
    """
    h8 = sha256_truncated(header_payload, 8)
    c8 = crc8(header_payload + h8)
    return (h8, c8)


def verify_mmp_trailer(header_payload: bytes, hash8: bytes, crc8_val: int) -> bool:
    """Verify trailer integrity."""
    expected_h8, expected_c8 = compute_mmp_trailer(header_payload)
    return hash8 == expected_h8 and crc8_val == expected_c8


def ed25519_sign(data: bytes, private_key: Optional[bytes] = None) -> Optional[bytes]:
    """
    Ed25519 sign (stub - returns None).
    Future: use nacl or cryptography for full signing.
    """
    return None


def ed25519_verify(data: bytes, signature: bytes, public_key: bytes) -> bool:
    """
    Ed25519 verify (stub - returns False).
    Future: implement when signing is required.
    """
    return False
