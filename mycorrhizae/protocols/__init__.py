"""
Mycosoft Device Protocol (MDP) and Mycosoft Mycorrhizae Protocol (MMP) implementations.

MDP v1: Binary protocol for MycoBrain devices with COBS framing and CRC-16.
MMP v1: Evolved protocol with enhanced header, SHA-256 integrity, and richer payload types.

(c) 2026 Mycosoft Labs
"""

from .mdp_types import (
    MDP_MAGIC,
    MDP_VER,
    MDPMessageType,
    MDPFlags,
    MDPEndpoint,
    MDPv1Header,
    MDPv1Frame,
)
from .mdp_framing import COBSCodec, CRC16Calculator
from .mdp_v1 import MDPv1Encoder, MDPv1Decoder
from .mmp_types import MMPDeviceType, MMPPayloadType, MMPv1Frame, MMPv1Header
from .mmp_v1 import MMPv1Encoder, MMPv1Decoder

__all__ = [
    # Constants
    "MDP_MAGIC",
    "MDP_VER",
    # Types
    "MDPMessageType",
    "MDPFlags",
    "MDPEndpoint",
    "MDPv1Header",
    "MDPv1Frame",
    # Framing
    "COBSCodec",
    "CRC16Calculator",
    # Protocol
    "MDPv1Encoder",
    "MDPv1Decoder",
    # MMP v1
    "MMPDeviceType",
    "MMPPayloadType",
    "MMPv1Header",
    "MMPv1Frame",
    "MMPv1Encoder",
    "MMPv1Decoder",
]
