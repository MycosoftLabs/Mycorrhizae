"""
Fungal Computer Interface (FCI) Module

Hardware interface for mycelium computing - enabling interaction
with biological systems through bioelectric signals.
"""

from .interface import (
    FCISignalType,
    FCIReading,
    FCIChannel,
    FCIInterface,
)
from .patterns import (
    PatternType,
    SignalPattern,
    PatternDetector,
)

__all__ = [
    "FCISignalType",
    "FCIReading",
    "FCIChannel",
    "FCIInterface",
    "PatternType",
    "SignalPattern",
    "PatternDetector",
]
