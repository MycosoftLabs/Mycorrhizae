"""
Mycorrhizae Protocol Module

Core protocol implementation for biological computing communication.

Components:
- envelope: Message envelope format with cryptographic signing
- semantic: Semantic translation layer for pattern interpretation
- protocol_main: Main MycorrhizaeProtocol router class

Version: 1.0.0

(c) 2026 Mycosoft Labs
"""

# Re-export main protocol router (from protocol_main to avoid shadowing this package)
from ..protocol_main import (
    MycorrhizaeProtocol,
    get_protocol,
    set_protocol,
)

from .envelope import (
    # Constants
    PROTOCOL_VERSION,
    DEFAULT_TTL_SECONDS,
    MAX_MESSAGE_SIZE_BYTES,
    # Enums
    SourceType,
    MessageType,
    ProbeType,
    # Data classes
    GeoLocation,
    Source,
    Signature,
    BioelectricChannelData,
    PatternData,
    EnvironmentData,
    FCITelemetryPayload,
    PatternEventPayload,
    StimulusCommandPayload,
    # Main envelope
    MycorrhizaeEnvelope,
    EnvelopeFactory,
)

from .semantic import (
    # Enums
    SemanticCategory,
    SemanticConfidence,
    TemporalPhase,
    # Data classes
    PatternSignature,
    SemanticInterpretation,
    # Pattern library
    GFST_PATTERN_LIBRARY,
    # Main translator
    SemanticTranslator,
    # Convenience functions
    get_translator,
    translate_pattern,
)

__all__ = [
    # Main protocol
    "MycorrhizaeProtocol",
    "get_protocol",
    "set_protocol",
    # Envelope constants
    "PROTOCOL_VERSION",
    "DEFAULT_TTL_SECONDS",
    "MAX_MESSAGE_SIZE_BYTES",
    # Envelope enums
    "SourceType",
    "MessageType",
    "ProbeType",
    # Envelope data classes
    "GeoLocation",
    "Source",
    "Signature",
    "BioelectricChannelData",
    "PatternData",
    "EnvironmentData",
    "FCITelemetryPayload",
    "PatternEventPayload",
    "StimulusCommandPayload",
    # Envelope
    "MycorrhizaeEnvelope",
    "EnvelopeFactory",
    # Semantic enums
    "SemanticCategory",
    "SemanticConfidence",
    "TemporalPhase",
    # Semantic data
    "PatternSignature",
    "SemanticInterpretation",
    "GFST_PATTERN_LIBRARY",
    # Semantic translator
    "SemanticTranslator",
    "get_translator",
    "translate_pattern",
]
