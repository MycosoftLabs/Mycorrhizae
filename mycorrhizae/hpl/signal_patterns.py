"""
HPL Signal Pattern Language (SPL) - Pattern Definition and Matching

The Signal Pattern Language is a sub-language within HPL for defining,
detecting, and matching bioelectric signal patterns from mycelium.

Example SPL pattern definition:

    pattern GrowthSignal {
        amplitude: 0.5 - 1.0 mV;
        frequency: 0.1 - 5 Hz;
        waveform: quasi-periodic;
        duration: > 1000 ms;
    }
    
    if (match(signalData, GrowthSignal)) {
        emit("growth_detected", signalData)
    }

Physics basis:
- Signal amplitude: Membrane potential changes (0.1-5 mV typical)
- Frequency: Ion channel kinetics (0.01-50 Hz range)
- Waveform: Action potential-like spikes vs oscillations

(c) 2026 Mycosoft Labs
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID, uuid4
import math
import re


# ============================================================================
# PATTERN LANGUAGE TYPES
# ============================================================================

class SignalUnit(str, Enum):
    """Units for signal measurements."""
    # Voltage
    VOLT = "V"
    MILLIVOLT = "mV"
    MICROVOLT = "uV"
    NANOVOLT = "nV"
    
    # Frequency
    HERTZ = "Hz"
    MILLIHERTZ = "mHz"
    KILOHERTZ = "kHz"
    
    # Time
    SECOND = "s"
    MILLISECOND = "ms"
    MICROSECOND = "us"
    MINUTE = "min"
    HOUR = "h"
    
    # Resistance
    OHM = "Ohm"
    KILOHM = "kOhm"
    MEGOHM = "MOhm"
    
    # Power
    WATT = "W"
    MILLIWATT = "mW"
    MICROWATT = "uW"
    DECIBEL = "dB"


class WaveformType(str, Enum):
    """Types of waveforms in bioelectric signals."""
    SPIKE = "spike"                 # Action potential-like
    OSCILLATION = "oscillation"     # Regular periodic
    QUASI_PERIODIC = "quasi-periodic"  # Somewhat regular
    APERIODIC = "aperiodic"        # Irregular
    BURST = "burst"                 # Multiple rapid events
    RAMP = "ramp"                   # Gradual increase
    DECAY = "decay"                 # Gradual decrease
    PLATEAU = "plateau"             # Stable level
    SINUSOIDAL = "sinusoidal"      # Pure sine wave
    SQUARE = "square"               # Square wave
    ANY = "any"                     # Match any waveform


class ComparisonOp(str, Enum):
    """Comparison operators for pattern matching."""
    EQ = "=="      # Equal
    NE = "!="      # Not equal
    LT = "<"       # Less than
    GT = ">"       # Greater than
    LE = "<="      # Less than or equal
    GE = ">="      # Greater than or equal
    IN = "in"      # In range
    APPROX = "~="  # Approximately equal (within tolerance)


# ============================================================================
# SIGNAL DATA TYPE
# ============================================================================

@dataclass
class Signal:
    """
    The Signal data type for HPL.
    
    Represents a bioelectric signal with its properties.
    This is the fundamental data type for signal processing in HPL.
    """
    
    # Core signal data
    samples: List[float] = field(default_factory=list)
    sample_rate_hz: float = 256.0
    
    # Computed properties (updated when samples change)
    amplitude_uv: float = 0.0      # Peak-to-peak amplitude
    frequency_hz: float = 0.0      # Dominant frequency
    phase_rad: float = 0.0         # Phase offset
    waveform: WaveformType = WaveformType.ANY
    
    # Time properties
    duration_ms: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Statistical properties
    mean: float = 0.0
    std: float = 0.0
    rms: float = 0.0
    snr_db: float = 0.0
    
    # Metadata
    channel_id: Optional[str] = None
    device_id: Optional[str] = None
    probe_type: Optional[str] = None
    
    def __post_init__(self):
        """Compute derived properties from samples."""
        if self.samples:
            self.compute_properties()
    
    def compute_properties(self):
        """Compute signal properties from sample data."""
        if not self.samples:
            return
        
        n = len(self.samples)
        
        # Time domain
        self.mean = sum(self.samples) / n
        self.std = math.sqrt(sum((x - self.mean)**2 for x in self.samples) / n)
        self.rms = math.sqrt(sum(x**2 for x in self.samples) / n)
        self.amplitude_uv = max(self.samples) - min(self.samples)
        self.duration_ms = (n / self.sample_rate_hz) * 1000
        
        # Estimate dominant frequency (zero-crossing method)
        crossings = 0
        mean_centered = [x - self.mean for x in self.samples]
        for i in range(1, n):
            if mean_centered[i-1] * mean_centered[i] < 0:
                crossings += 1
        
        if crossings > 1:
            periods = crossings / 2
            self.frequency_hz = periods / (self.duration_ms / 1000)
        
        # Classify waveform
        self._classify_waveform()
    
    def _classify_waveform(self):
        """Classify the waveform type based on signal properties."""
        if not self.samples:
            self.waveform = WaveformType.ANY
            return
        
        n = len(self.samples)
        
        # Check for spikes (high amplitude, short duration events)
        if self.amplitude_uv > 3 * self.std and self.frequency_hz < 1:
            self.waveform = WaveformType.SPIKE
        
        # Check for regularity (coefficient of variation of intervals)
        elif self.frequency_hz > 0.1 and self.std < self.amplitude_uv / 3:
            # Calculate interval consistency
            self.waveform = WaveformType.OSCILLATION
        
        # Check for trends
        elif len(self.samples) > 10:
            start_avg = sum(self.samples[:5]) / 5
            end_avg = sum(self.samples[-5:]) / 5
            
            if end_avg > start_avg * 1.5:
                self.waveform = WaveformType.RAMP
            elif end_avg < start_avg * 0.5:
                self.waveform = WaveformType.DECAY
            elif abs(end_avg - start_avg) < self.std:
                self.waveform = WaveformType.PLATEAU
            else:
                self.waveform = WaveformType.APERIODIC
        else:
            self.waveform = WaveformType.APERIODIC
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "sample_count": len(self.samples),
            "sample_rate_hz": self.sample_rate_hz,
            "amplitude_uv": self.amplitude_uv,
            "frequency_hz": self.frequency_hz,
            "phase_rad": self.phase_rad,
            "waveform": self.waveform.value,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat(),
            "mean": self.mean,
            "std": self.std,
            "rms": self.rms,
            "snr_db": self.snr_db,
            "channel_id": self.channel_id,
            "device_id": self.device_id,
        }


# ============================================================================
# PATTERN CONSTRAINT
# ============================================================================

@dataclass
class PatternConstraint:
    """
    A single constraint within a pattern definition.
    
    Examples:
        amplitude: 0.5 - 1.0 mV;
        frequency: > 0.1 Hz;
        waveform: quasi-periodic;
    """
    
    property_name: str              # e.g., "amplitude", "frequency"
    comparison: ComparisonOp        # e.g., IN, GT, EQ
    value: Union[float, Tuple[float, float], str, WaveformType]
    unit: Optional[SignalUnit] = None
    tolerance: float = 0.0          # For approximate matching
    weight: float = 1.0             # Importance in matching (0-1)
    
    def matches(self, signal: Signal) -> Tuple[bool, float]:
        """
        Check if signal matches this constraint.
        
        Returns:
            Tuple of (matched: bool, confidence: float)
        """
        # Get the signal property value
        signal_value = self._get_signal_property(signal)
        if signal_value is None:
            return False, 0.0
        
        # Convert units if needed
        signal_value = self._convert_units(signal_value)
        
        # Perform comparison
        return self._compare(signal_value)
    
    def _get_signal_property(self, signal: Signal) -> Optional[Union[float, str]]:
        """Extract the relevant property from the signal."""
        property_map = {
            "amplitude": signal.amplitude_uv,
            "amplitude_uv": signal.amplitude_uv,
            "frequency": signal.frequency_hz,
            "frequency_hz": signal.frequency_hz,
            "phase": signal.phase_rad,
            "phase_rad": signal.phase_rad,
            "waveform": signal.waveform.value,
            "duration": signal.duration_ms,
            "duration_ms": signal.duration_ms,
            "mean": signal.mean,
            "std": signal.std,
            "rms": signal.rms,
            "snr": signal.snr_db,
            "snr_db": signal.snr_db,
        }
        
        return property_map.get(self.property_name.lower())
    
    def _convert_units(self, value: float) -> float:
        """Convert value to base units for comparison."""
        if self.unit is None:
            return value
        
        # Unit conversion factors to base units (uV for voltage, Hz for freq, ms for time)
        conversions = {
            SignalUnit.VOLT: 1e6,         # V to uV
            SignalUnit.MILLIVOLT: 1e3,    # mV to uV
            SignalUnit.MICROVOLT: 1,      # uV to uV
            SignalUnit.NANOVOLT: 1e-3,    # nV to uV
            SignalUnit.HERTZ: 1,          # Hz to Hz
            SignalUnit.MILLIHERTZ: 1e-3,  # mHz to Hz
            SignalUnit.KILOHERTZ: 1e3,    # kHz to Hz
            SignalUnit.SECOND: 1000,      # s to ms
            SignalUnit.MILLISECOND: 1,    # ms to ms
            SignalUnit.MICROSECOND: 1e-3, # us to ms
            SignalUnit.MINUTE: 60000,     # min to ms
            SignalUnit.HOUR: 3600000,     # h to ms
        }
        
        factor = conversions.get(self.unit, 1)
        
        # Apply to value(s) in constraint
        if isinstance(self.value, tuple):
            return value  # Signal value, not constraint value
        return value
    
    def _compare(self, signal_value: Union[float, str]) -> Tuple[bool, float]:
        """Perform the comparison operation."""
        
        # Handle waveform matching (string comparison)
        if isinstance(signal_value, str):
            if self.comparison == ComparisonOp.EQ:
                matches = signal_value == self.value or self.value == WaveformType.ANY.value
                return matches, 1.0 if matches else 0.0
            elif self.comparison == ComparisonOp.NE:
                matches = signal_value != self.value
                return matches, 1.0 if matches else 0.0
            return False, 0.0
        
        # Handle numeric comparisons
        constraint_value = self.value
        
        # Convert constraint value units
        if self.unit:
            conversions = {
                SignalUnit.VOLT: 1e6,
                SignalUnit.MILLIVOLT: 1e3,
                SignalUnit.MICROVOLT: 1,
                SignalUnit.HERTZ: 1,
                SignalUnit.MILLIHERTZ: 1e-3,
                SignalUnit.SECOND: 1000,
                SignalUnit.MILLISECOND: 1,
            }
            factor = conversions.get(self.unit, 1)
            
            if isinstance(constraint_value, tuple):
                constraint_value = (constraint_value[0] * factor, constraint_value[1] * factor)
            elif isinstance(constraint_value, (int, float)):
                constraint_value = constraint_value * factor
        
        # Comparison operations
        if self.comparison == ComparisonOp.EQ:
            if self.tolerance > 0:
                matches = abs(signal_value - constraint_value) <= self.tolerance
            else:
                matches = signal_value == constraint_value
            confidence = 1.0 if matches else 0.0
            
        elif self.comparison == ComparisonOp.NE:
            matches = signal_value != constraint_value
            confidence = 1.0 if matches else 0.0
            
        elif self.comparison == ComparisonOp.LT:
            matches = signal_value < constraint_value
            if matches:
                confidence = 1.0 - (signal_value / constraint_value) if constraint_value > 0 else 1.0
            else:
                confidence = 0.0
                
        elif self.comparison == ComparisonOp.GT:
            matches = signal_value > constraint_value
            if matches:
                confidence = min(1.0, signal_value / constraint_value) if constraint_value > 0 else 1.0
            else:
                confidence = 0.0
                
        elif self.comparison == ComparisonOp.LE:
            matches = signal_value <= constraint_value
            confidence = 1.0 if matches else 0.0
            
        elif self.comparison == ComparisonOp.GE:
            matches = signal_value >= constraint_value
            confidence = 1.0 if matches else 0.0
            
        elif self.comparison == ComparisonOp.IN:
            # Range comparison
            if isinstance(constraint_value, tuple):
                low, high = constraint_value
                matches = low <= signal_value <= high
                if matches:
                    # Confidence based on how centered the value is
                    mid = (low + high) / 2
                    range_half = (high - low) / 2
                    confidence = 1.0 - abs(signal_value - mid) / range_half if range_half > 0 else 1.0
                else:
                    confidence = 0.0
            else:
                matches = False
                confidence = 0.0
                
        elif self.comparison == ComparisonOp.APPROX:
            # Approximate matching with tolerance
            if self.tolerance > 0:
                diff = abs(signal_value - constraint_value)
                matches = diff <= self.tolerance
                confidence = 1.0 - (diff / self.tolerance) if matches else 0.0
            else:
                # Default 10% tolerance
                tolerance = abs(constraint_value * 0.1)
                diff = abs(signal_value - constraint_value)
                matches = diff <= tolerance
                confidence = 1.0 - (diff / tolerance) if tolerance > 0 and matches else (1.0 if matches else 0.0)
        else:
            matches = False
            confidence = 0.0
        
        return matches, confidence


# ============================================================================
# PATTERN DEFINITION
# ============================================================================

@dataclass
class Pattern:
    """
    A complete pattern definition for signal matching.
    
    Example HPL syntax:
        pattern GrowthSignal {
            amplitude: 0.5 - 1.0 mV;
            frequency: 0.1 - 5 Hz;
            waveform: quasi-periodic;
            duration: > 1000 ms;
        }
    """
    
    name: str
    constraints: List[PatternConstraint] = field(default_factory=list)
    description: str = ""
    category: str = "custom"          # e.g., "growth", "stress", "seismic"
    priority: int = 0                 # Higher = checked first
    min_confidence: float = 0.6       # Minimum confidence for match
    
    # Temporal requirements
    min_duration_ms: float = 0
    max_duration_ms: float = float('inf')
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    author: str = ""
    version: str = "1.0"
    
    def add_constraint(
        self,
        property_name: str,
        comparison: ComparisonOp,
        value: Union[float, Tuple[float, float], str],
        unit: Optional[SignalUnit] = None,
        weight: float = 1.0,
    ) -> "Pattern":
        """Add a constraint to the pattern (fluent interface)."""
        self.constraints.append(PatternConstraint(
            property_name=property_name,
            comparison=comparison,
            value=value,
            unit=unit,
            weight=weight,
        ))
        return self
    
    def match(self, signal: Signal) -> Tuple[bool, float]:
        """
        Match a signal against this pattern.
        
        Returns:
            Tuple of (matched: bool, confidence: float)
        """
        if not self.constraints:
            return False, 0.0
        
        # Check duration constraints
        if signal.duration_ms < self.min_duration_ms:
            return False, 0.0
        if signal.duration_ms > self.max_duration_ms:
            return False, 0.0
        
        # Match all constraints
        total_weight = 0.0
        weighted_confidence = 0.0
        all_matched = True
        
        for constraint in self.constraints:
            matched, confidence = constraint.matches(signal)
            
            if not matched:
                all_matched = False
            
            weighted_confidence += confidence * constraint.weight
            total_weight += constraint.weight
        
        # Calculate overall confidence
        if total_weight > 0:
            overall_confidence = weighted_confidence / total_weight
        else:
            overall_confidence = 0.0
        
        # Pattern matches if all constraints match OR confidence is above threshold
        pattern_matched = all_matched or overall_confidence >= self.min_confidence
        
        return pattern_matched, overall_confidence
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "constraints": [
                {
                    "property": c.property_name,
                    "comparison": c.comparison.value,
                    "value": c.value if not isinstance(c.value, tuple) else list(c.value),
                    "unit": c.unit.value if c.unit else None,
                    "weight": c.weight,
                }
                for c in self.constraints
            ],
            "min_confidence": self.min_confidence,
            "min_duration_ms": self.min_duration_ms,
            "max_duration_ms": self.max_duration_ms if self.max_duration_ms != float('inf') else None,
            "version": self.version,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pattern":
        """Create pattern from dictionary."""
        pattern = cls(
            name=data["name"],
            description=data.get("description", ""),
            category=data.get("category", "custom"),
            min_confidence=data.get("min_confidence", 0.6),
            min_duration_ms=data.get("min_duration_ms", 0),
            max_duration_ms=data.get("max_duration_ms") or float('inf'),
            version=data.get("version", "1.0"),
        )
        
        for c in data.get("constraints", []):
            value = c["value"]
            if isinstance(value, list) and len(value) == 2:
                value = tuple(value)
            
            pattern.constraints.append(PatternConstraint(
                property_name=c["property"],
                comparison=ComparisonOp(c["comparison"]),
                value=value,
                unit=SignalUnit(c["unit"]) if c.get("unit") else None,
                weight=c.get("weight", 1.0),
            ))
        
        return pattern


# ============================================================================
# PATTERN LIBRARY (Built-in GFST patterns)
# ============================================================================

# Pre-defined patterns based on Global Fungi Symbiosis Theory
GFST_PATTERN_LIBRARY: Dict[str, Pattern] = {
    "GrowthSignal": Pattern(
        name="GrowthSignal",
        description="Active hyphal extension signal - quasi-periodic low-frequency oscillations",
        category="growth",
        constraints=[
            PatternConstraint("amplitude", ComparisonOp.IN, (0.5, 2.0), SignalUnit.MICROVOLT),
            PatternConstraint("frequency", ComparisonOp.IN, (0.1, 5.0), SignalUnit.HERTZ),
            PatternConstraint("waveform", ComparisonOp.EQ, WaveformType.QUASI_PERIODIC.value),
        ],
        min_confidence=0.6,
        min_duration_ms=1000,
    ),
    
    "StressResponse": Pattern(
        name="StressResponse",
        description="Environmental stress signal - elevated frequency and amplitude",
        category="stress",
        constraints=[
            PatternConstraint("amplitude", ComparisonOp.GT, 1.0, SignalUnit.MICROVOLT),
            PatternConstraint("frequency", ComparisonOp.IN, (5.0, 20.0), SignalUnit.HERTZ),
            PatternConstraint("waveform", ComparisonOp.EQ, WaveformType.APERIODIC.value),
        ],
        min_confidence=0.5,
    ),
    
    "NutrientSeeking": Pattern(
        name="NutrientSeeking",
        description="Chemotropic navigation signal - sustained oscillations",
        category="navigation",
        constraints=[
            PatternConstraint("amplitude", ComparisonOp.IN, (0.3, 1.5), SignalUnit.MICROVOLT),
            PatternConstraint("frequency", ComparisonOp.IN, (0.5, 3.0), SignalUnit.HERTZ),
            PatternConstraint("waveform", ComparisonOp.EQ, WaveformType.OSCILLATION.value),
        ],
        min_confidence=0.6,
        min_duration_ms=5000,
    ),
    
    "ActionPotential": Pattern(
        name="ActionPotential",
        description="Spike-like event similar to neuronal action potentials",
        category="spike",
        constraints=[
            PatternConstraint("amplitude", ComparisonOp.GT, 2.0, SignalUnit.MICROVOLT),
            PatternConstraint("waveform", ComparisonOp.EQ, WaveformType.SPIKE.value),
            PatternConstraint("duration", ComparisonOp.IN, (5, 100), SignalUnit.MILLISECOND),
        ],
        min_confidence=0.7,
        min_duration_ms=5,
        max_duration_ms=200,
    ),
    
    "SeismicPrecursor": Pattern(
        name="SeismicPrecursor",
        description="M-Wave earthquake precursor - very low frequency impedance changes",
        category="seismic",
        constraints=[
            PatternConstraint("frequency", ComparisonOp.IN, (0.01, 0.1), SignalUnit.HERTZ),
            PatternConstraint("waveform", ComparisonOp.EQ, WaveformType.APERIODIC.value),
        ],
        min_confidence=0.5,
        min_duration_ms=3600000,  # 1 hour minimum
        priority=10,  # High priority - check first
    ),
    
    "SymbioticExchange": Pattern(
        name="SymbioticExchange",
        description="Plant-fungal nutrient exchange signal",
        category="symbiotic",
        constraints=[
            PatternConstraint("amplitude", ComparisonOp.IN, (0.2, 1.0), SignalUnit.MICROVOLT),
            PatternConstraint("frequency", ComparisonOp.IN, (0.05, 0.5), SignalUnit.HERTZ),
            PatternConstraint("waveform", ComparisonOp.EQ, WaveformType.OSCILLATION.value),
        ],
        min_confidence=0.6,
    ),
    
    "Baseline": Pattern(
        name="Baseline",
        description="Resting electrical activity",
        category="baseline",
        constraints=[
            PatternConstraint("amplitude", ComparisonOp.LT, 0.3, SignalUnit.MICROVOLT),
            PatternConstraint("frequency", ComparisonOp.LT, 0.5, SignalUnit.HERTZ),
        ],
        min_confidence=0.8,
        priority=-1,  # Low priority - check last
    ),
}


# ============================================================================
# PATTERN MATCHER (HPL match() function)
# ============================================================================

class PatternMatcher:
    """
    Pattern matching engine for HPL.
    
    Provides the match() function for HPL programs:
        if (match(signalData, GrowthSignal)) { ... }
    """
    
    def __init__(self):
        self.patterns: Dict[str, Pattern] = {}
        self.match_history: List[Dict[str, Any]] = []
        
        # Load built-in patterns
        for name, pattern in GFST_PATTERN_LIBRARY.items():
            self.patterns[name] = pattern
    
    def register_pattern(self, pattern: Pattern) -> None:
        """Register a new pattern."""
        self.patterns[pattern.name] = pattern
    
    def get_pattern(self, name: str) -> Optional[Pattern]:
        """Get a pattern by name."""
        return self.patterns.get(name)
    
    def match(
        self,
        signal: Signal,
        pattern_name: str,
    ) -> Tuple[bool, float]:
        """
        Match a signal against a named pattern.
        
        This is the implementation of HPL's match() function.
        
        Args:
            signal: The signal to match
            pattern_name: Name of the pattern to match against
            
        Returns:
            Tuple of (matched: bool, confidence: float)
        """
        pattern = self.patterns.get(pattern_name)
        if not pattern:
            return False, 0.0
        
        matched, confidence = pattern.match(signal)
        
        # Record match attempt
        self.match_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pattern": pattern_name,
            "matched": matched,
            "confidence": confidence,
            "signal_summary": {
                "amplitude_uv": signal.amplitude_uv,
                "frequency_hz": signal.frequency_hz,
                "duration_ms": signal.duration_ms,
                "waveform": signal.waveform.value,
            }
        })
        
        return matched, confidence
    
    def match_all(
        self,
        signal: Signal,
    ) -> List[Tuple[str, bool, float]]:
        """
        Match signal against all registered patterns.
        
        Returns:
            List of (pattern_name, matched, confidence) sorted by confidence
        """
        results = []
        
        # Sort patterns by priority (higher first)
        sorted_patterns = sorted(
            self.patterns.items(),
            key=lambda x: x[1].priority,
            reverse=True
        )
        
        for name, pattern in sorted_patterns:
            matched, confidence = pattern.match(signal)
            results.append((name, matched, confidence))
        
        # Sort by confidence
        results.sort(key=lambda x: x[2], reverse=True)
        
        return results
    
    def best_match(
        self,
        signal: Signal,
    ) -> Optional[Tuple[str, float]]:
        """
        Find the best matching pattern for a signal.
        
        Returns:
            Tuple of (pattern_name, confidence) or None if no match
        """
        matches = self.match_all(signal)
        
        for name, matched, confidence in matches:
            if matched:
                return name, confidence
        
        return None
    
    def list_patterns(self) -> List[Dict[str, Any]]:
        """List all registered patterns."""
        return [
            {
                "name": p.name,
                "category": p.category,
                "description": p.description,
                "constraint_count": len(p.constraints),
                "min_confidence": p.min_confidence,
            }
            for p in self.patterns.values()
        ]


# ============================================================================
# PATTERN PARSER (Parse pattern definitions from HPL source)
# ============================================================================

class PatternParser:
    """
    Parses pattern definitions from HPL source code.
    
    Example input:
        pattern GrowthSignal {
            amplitude: 0.5 - 1.0 mV;
            frequency: 0.1 - 5 Hz;
            waveform: quasi-periodic;
        }
    """
    
    # Regex patterns
    PATTERN_DEF = re.compile(r'pattern\s+(\w+)\s*\{([^}]+)\}', re.MULTILINE | re.DOTALL)
    CONSTRAINT_LINE = re.compile(r'(\w+)\s*:\s*(.+?)\s*;')
    RANGE_VALUE = re.compile(r'([\d.]+)\s*-\s*([\d.]+)\s*(\w+)?')
    COMPARISON_VALUE = re.compile(r'([<>=!~]+)\s*([\d.]+)\s*(\w+)?')
    SIMPLE_VALUE = re.compile(r'([\d.]+)\s*(\w+)?')
    
    def parse(self, source: str) -> List[Pattern]:
        """Parse pattern definitions from HPL source."""
        patterns = []
        
        for match in self.PATTERN_DEF.finditer(source):
            name = match.group(1)
            body = match.group(2)
            
            pattern = Pattern(name=name)
            
            for constraint_match in self.CONSTRAINT_LINE.finditer(body):
                prop_name = constraint_match.group(1)
                value_str = constraint_match.group(2).strip()
                
                constraint = self._parse_constraint(prop_name, value_str)
                if constraint:
                    pattern.constraints.append(constraint)
            
            patterns.append(pattern)
        
        return patterns
    
    def _parse_constraint(self, prop_name: str, value_str: str) -> Optional[PatternConstraint]:
        """Parse a single constraint line."""
        
        # Try range: "0.5 - 1.0 mV"
        range_match = self.RANGE_VALUE.match(value_str)
        if range_match:
            low = float(range_match.group(1))
            high = float(range_match.group(2))
            unit_str = range_match.group(3)
            unit = self._parse_unit(unit_str) if unit_str else None
            
            return PatternConstraint(
                property_name=prop_name,
                comparison=ComparisonOp.IN,
                value=(low, high),
                unit=unit,
            )
        
        # Try comparison: "> 0.1 Hz"
        comp_match = self.COMPARISON_VALUE.match(value_str)
        if comp_match:
            op_str = comp_match.group(1)
            value = float(comp_match.group(2))
            unit_str = comp_match.group(3)
            
            op_map = {
                "==": ComparisonOp.EQ,
                "!=": ComparisonOp.NE,
                "<": ComparisonOp.LT,
                ">": ComparisonOp.GT,
                "<=": ComparisonOp.LE,
                ">=": ComparisonOp.GE,
                "~=": ComparisonOp.APPROX,
            }
            comparison = op_map.get(op_str, ComparisonOp.EQ)
            unit = self._parse_unit(unit_str) if unit_str else None
            
            return PatternConstraint(
                property_name=prop_name,
                comparison=comparison,
                value=value,
                unit=unit,
            )
        
        # Try simple numeric: "1.0 mV"
        simple_match = self.SIMPLE_VALUE.match(value_str)
        if simple_match:
            value = float(simple_match.group(1))
            unit_str = simple_match.group(2)
            unit = self._parse_unit(unit_str) if unit_str else None
            
            return PatternConstraint(
                property_name=prop_name,
                comparison=ComparisonOp.EQ,
                value=value,
                unit=unit,
            )
        
        # Try waveform type
        waveform_values = [w.value for w in WaveformType]
        if value_str.lower().replace("-", "-") in waveform_values:
            return PatternConstraint(
                property_name=prop_name,
                comparison=ComparisonOp.EQ,
                value=value_str.lower(),
            )
        
        return None
    
    def _parse_unit(self, unit_str: str) -> Optional[SignalUnit]:
        """Parse a unit string."""
        unit_map = {
            "v": SignalUnit.VOLT,
            "mv": SignalUnit.MILLIVOLT,
            "uv": SignalUnit.MICROVOLT,
            "µv": SignalUnit.MICROVOLT,
            "hz": SignalUnit.HERTZ,
            "mhz": SignalUnit.MILLIHERTZ,
            "khz": SignalUnit.KILOHERTZ,
            "s": SignalUnit.SECOND,
            "ms": SignalUnit.MILLISECOND,
            "us": SignalUnit.MICROSECOND,
            "µs": SignalUnit.MICROSECOND,
            "min": SignalUnit.MINUTE,
            "h": SignalUnit.HOUR,
            "ohm": SignalUnit.OHM,
            "kohm": SignalUnit.KILOHM,
            "mohm": SignalUnit.MEGOHM,
            "db": SignalUnit.DECIBEL,
        }
        
        return unit_map.get(unit_str.lower())


# ============================================================================
# HPL BUILT-IN FUNCTIONS
# ============================================================================

# Global pattern matcher instance
_global_matcher = PatternMatcher()


def match(signal: Signal, pattern_name: str) -> bool:
    """
    HPL match() function - check if signal matches a pattern.
    
    Usage in HPL:
        if (match(signalData, "GrowthSignal")) { ... }
    """
    matched, _ = _global_matcher.match(signal, pattern_name)
    return matched


def correlation(signal: Signal, pattern_name: str) -> float:
    """
    HPL correlation() function - get match confidence.
    
    Usage in HPL:
        confidence = correlation(signalData, GrowthSignal)
    """
    _, confidence = _global_matcher.match(signal, pattern_name)
    return confidence


def best_pattern(signal: Signal) -> Optional[str]:
    """
    HPL best_pattern() function - find best matching pattern.
    
    Usage in HPL:
        pattern_name = best_pattern(signalData)
    """
    result = _global_matcher.best_match(signal)
    return result[0] if result else None


def register_pattern(pattern: Pattern) -> None:
    """Register a custom pattern with the global matcher."""
    _global_matcher.register_pattern(pattern)


def get_pattern_matcher() -> PatternMatcher:
    """Get the global pattern matcher instance."""
    return _global_matcher
