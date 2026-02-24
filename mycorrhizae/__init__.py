"""
Mycorrhizae Protocol - Biological Computing Communication Protocol

The Mycorrhizae Protocol is a novel biological computing communication protocol 
designed for bidirectional information exchange between computational systems 
and fungal mycelial networks. Unlike conventional IoT protocols that merely 
route raw sensor data, Mycorrhizae interprets bioelectric signals through the 
lens of Global Fungi Symbiosis Theory (GFST), translating fungal responses 
into semantically meaningful information.

This protocol is the first of its kind: a bridge between biological 
intelligence and digital computation.

Modules:
- message: Legacy message types (compatibility)
- protocol: Legacy protocol implementation (compatibility)
- channels: Channel management for pub/sub
- fci: Fungal Computer Interface hardware abstraction
- hpl: Hypha Programming Language interpreter
- protocol: Novel envelope format and semantic translation
- mwave: Earthquake analysis (GFST application)

Version: 1.0.0
(c) 2026 Mycosoft Labs
"""

__version__ = "1.0.0"

# Legacy compatibility
from .message import MycorrhizaeMessage, MessageType, SourceType
from .protocol import MycorrhizaeProtocol
from .channels import Channel, ChannelType, ChannelManager

# Novel Mycorrhizae Protocol v1.0
from .protocol import (
    MycorrhizaeEnvelope,
    EnvelopeFactory,
    PROTOCOL_VERSION,
    SemanticTranslator,
    translate_pattern,
    GFST_PATTERN_LIBRARY,
)

# FCI - Fungal Computer Interface
from . import fci
from . import hpl
from . import mwave

# MDP/MMP protocols
from . import protocols

# Device gateway
from . import gateway

# Client SDK
from . import client

__all__ = [
    # Version
    "__version__",
    # Legacy
    "MycorrhizaeMessage",
    "MessageType",
    "SourceType",
    "MycorrhizaeProtocol",
    "Channel",
    "ChannelType",
    "ChannelManager",
    # Novel Protocol
    "MycorrhizaeEnvelope",
    "EnvelopeFactory",
    "PROTOCOL_VERSION",
    "SemanticTranslator",
    "translate_pattern",
    "GFST_PATTERN_LIBRARY",
    # Sub-modules
    "fci",
    "hpl",
    "mwave",
    "protocols",
    "gateway",
    "client",
]
