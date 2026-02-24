"""
Shared MycoEnvelope v1 + replay ACK contract helpers.

This module centralizes envelope and ACK validation logic so protocol, MAS,
and downstream adapters can enforce the same contract.
"""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple


@dataclass
class EnvelopeValidationResult:
    valid: bool
    reason: Optional[str] = None
    device_id: Optional[str] = None
    msg_id: Optional[str] = None
    seq: Optional[int] = None


@dataclass
class ReplayAck:
    device_id: str
    msg_id: str
    seq: int
    accepted: bool
    reason: Optional[str] = None
    acked_at_utc: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "deviceId": self.device_id,
            "msgId": self.msg_id,
            "seq": self.seq,
            "accepted": self.accepted,
            "reason": self.reason,
            "ackedAtUtc": self.acked_at_utc
            or datetime.now(timezone.utc).isoformat(),
        }


def _canonical_unsigned_bytes(envelope: Dict[str, Any]) -> bytes:
    unsigned = {k: v for k, v in envelope.items() if k not in ("hash", "sig")}
    # Deterministic key ordering for cross-language digest consistency.
    return json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _parse_hash(hash_value: str) -> Optional[bytes]:
    if not isinstance(hash_value, str) or ":" not in hash_value:
        return None
    algo, hex_value = hash_value.split(":", 1)
    if algo.lower() not in {"sha256", "blake2b256", "blake2b"}:
        return None
    try:
        return bytes.fromhex(hex_value)
    except ValueError:
        return None


def validate_envelope_structure(envelope: Dict[str, Any]) -> EnvelopeValidationResult:
    required_keys = {"hdr", "ts", "seq", "pack", "hash", "sig"}
    missing = required_keys - set(envelope.keys())
    if missing:
        return EnvelopeValidationResult(False, f"missing_keys:{','.join(sorted(missing))}")

    hdr = envelope.get("hdr", {})
    msg_id = hdr.get("msgId")
    device_id = hdr.get("deviceId")
    if not device_id or not msg_id:
        return EnvelopeValidationResult(False, "missing_hdr_fields")

    seq = envelope.get("seq")
    if not isinstance(seq, int) or seq < 0:
        return EnvelopeValidationResult(False, "invalid_seq", device_id=device_id, msg_id=msg_id)

    pack = envelope.get("pack")
    if not isinstance(pack, list):
        return EnvelopeValidationResult(False, "invalid_pack", device_id=device_id, msg_id=msg_id, seq=seq)

    return EnvelopeValidationResult(True, device_id=device_id, msg_id=msg_id, seq=seq)


def verify_envelope_hash(envelope: Dict[str, Any]) -> Tuple[bool, str]:
    hash_value = envelope.get("hash")
    expected = _parse_hash(hash_value)
    if not expected:
        return False, "invalid_hash_field"

    unsigned = _canonical_unsigned_bytes(envelope)
    computed = hashlib.sha256(unsigned).digest()

    # For compatibility with blake2b256 rollout, accept either when declared.
    algo = hash_value.split(":", 1)[0].lower()
    if algo in {"blake2b256", "blake2b"}:
        computed = hashlib.blake2b(unsigned, digest_size=32).digest()

    if computed != expected:
        return False, "hash_mismatch"
    return True, "ok"


def verify_ed25519_signature(sig_field: str, payload_hash: bytes, public_key_b64: str) -> Tuple[bool, str]:
    if not isinstance(sig_field, str) or ":" not in sig_field:
        return False, "invalid_sig_field"
    scheme, sig_value = sig_field.split(":", 1)
    if scheme.lower() != "ed25519":
        return False, "unsupported_signature_scheme"

    try:
        signature = base64.b64decode(sig_value)
        public_key_bytes = base64.b64decode(public_key_b64)
    except Exception:
        return False, "invalid_signature_encoding"

    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except Exception:
        return False, "ed25519_library_unavailable"

    try:
        verifier = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        verifier.verify(signature, b"MYCO1" + payload_hash)
        return True, "ok"
    except Exception:
        return False, "signature_mismatch"


def build_replay_ack(device_id: str, msg_id: str, seq: int, accepted: bool, reason: Optional[str] = None) -> Dict[str, Any]:
    return ReplayAck(
        device_id=device_id,
        msg_id=msg_id,
        seq=seq,
        accepted=accepted,
        reason=reason,
    ).to_dict()
