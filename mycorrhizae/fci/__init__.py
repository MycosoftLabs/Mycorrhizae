"""
Fungal Computer Interface (FCI) Module

Hardware interface for mycelium computing - enabling interaction
with biological systems through bioelectric signals.

Probe designs supported (Mycosoft FCI probes):
- Type A: Copper-steel differential with agar interface
- Type B: Silver/Silver-chloride reference electrode
- Type C: Platinum-iridium high-precision
- Type D: Carbon fiber for minimal interference

Based on Global Fungi Symbiosis Theory (GFST) research.
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
from .signal_processing import (
    ElectrodeMaterial,
    ProbeType,
    ElectrodeConfig,
    ProbeConfig,
    PROBE_CONFIGS,
    BiologicalPattern,
    PatternSignature,
    GFST_PATTERNS,
    ProcessedSignal,
    FCISignalProcessor,
    NetworkAnalyzer,
)

__all__ = [
    # Interface
    "FCISignalType",
    "FCIReading",
    "FCIChannel",
    "FCIInterface",
    # Patterns
    "PatternType",
    "SignalPattern",
    "PatternDetector",
    # Signal Processing
    "ElectrodeMaterial",
    "ProbeType",
    "ElectrodeConfig",
    "ProbeConfig",
    "PROBE_CONFIGS",
    "BiologicalPattern",
    "PatternSignature",
    "GFST_PATTERNS",
    "ProcessedSignal",
    "FCISignalProcessor",
    "NetworkAnalyzer",
]
