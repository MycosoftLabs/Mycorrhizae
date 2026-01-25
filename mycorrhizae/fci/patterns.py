"""
FCI Pattern Detection

Detects patterns in bioelectric signals from mycelium networks.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from .interface import FCIReading, FCISignalType


class PatternType(str, Enum):
    """Types of patterns detectable in FCI signals."""
    SPIKE = "spike"                 # Sudden increase in signal
    DROP = "drop"                   # Sudden decrease in signal
    OSCILLATION = "oscillation"     # Regular oscillating pattern
    RAMP = "ramp"                   # Gradual increase
    DECAY = "decay"                 # Gradual decrease
    PLATEAU = "plateau"             # Stable period
    BURST = "burst"                 # Multiple rapid spikes
    SYNCHRONIZED = "synchronized"   # Multiple channels in sync
    ANOMALY = "anomaly"             # Unusual pattern


@dataclass
class SignalPattern:
    """A detected pattern in FCI signals."""
    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    pattern_type: PatternType = PatternType.SPIKE
    
    # Pattern location
    channel_id: int = 0
    start_index: int = 0
    end_index: int = 0
    duration_ms: float = 0.0
    
    # Pattern characteristics
    amplitude: float = 0.0          # Peak amplitude
    frequency_hz: Optional[float] = None  # For oscillations
    confidence: float = 0.0         # Detection confidence (0-1)
    
    # Context
    baseline: float = 0.0           # Baseline before pattern
    peak_value: float = 0.0         # Peak value during pattern
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "pattern_type": self.pattern_type.value,
            "channel_id": self.channel_id,
            "duration_ms": self.duration_ms,
            "amplitude": self.amplitude,
            "frequency_hz": self.frequency_hz,
            "confidence": self.confidence,
            "baseline": self.baseline,
            "peak_value": self.peak_value,
            "metadata": self.metadata,
        }


class PatternDetector:
    """
    Detects patterns in FCI signals.
    
    Uses sliding window analysis to detect:
    - Spikes and drops (threshold-based)
    - Oscillations (frequency analysis)
    - Ramps and decays (trend analysis)
    - Bursts (spike counting)
    - Synchronized patterns (cross-channel correlation)
    """
    
    # Detection parameters
    SPIKE_THRESHOLD = 2.0       # Standard deviations for spike detection
    DROP_THRESHOLD = -2.0       # Standard deviations for drop detection
    OSCILLATION_MIN_PERIODS = 3 # Minimum oscillation periods to detect
    BURST_MIN_SPIKES = 3        # Minimum spikes for burst detection
    BURST_MAX_INTERVAL_MS = 500 # Maximum interval between burst spikes
    SYNC_CORRELATION_MIN = 0.7  # Minimum correlation for sync detection
    
    def __init__(self, window_size: int = 100, sample_rate_hz: float = 10.0):
        self.window_size = window_size
        self.sample_rate_hz = sample_rate_hz
        self.detected_patterns: List[SignalPattern] = []
    
    def analyze(self, readings: List[FCIReading]) -> List[SignalPattern]:
        """
        Analyze readings for patterns.
        
        Returns list of detected patterns.
        """
        if len(readings) < 10:
            return []
        
        patterns = []
        
        # Extract values
        values = [r.normalized_value for r in readings]
        
        # Calculate baseline statistics
        mean_val = sum(values) / len(values)
        variance = sum((v - mean_val) ** 2 for v in values) / len(values)
        std_val = variance ** 0.5 if variance > 0 else 0.001
        
        # Detect spikes and drops
        patterns.extend(self._detect_spikes(readings, values, mean_val, std_val))
        
        # Detect oscillations
        patterns.extend(self._detect_oscillations(readings, values))
        
        # Detect trends (ramps/decays)
        patterns.extend(self._detect_trends(readings, values))
        
        # Detect bursts
        patterns.extend(self._detect_bursts(readings, values, mean_val, std_val))
        
        self.detected_patterns.extend(patterns)
        
        return patterns
    
    def _detect_spikes(
        self,
        readings: List[FCIReading],
        values: List[float],
        mean_val: float,
        std_val: float,
    ) -> List[SignalPattern]:
        """Detect spike and drop patterns."""
        patterns = []
        
        for i, val in enumerate(values):
            z_score = (val - mean_val) / std_val if std_val > 0 else 0
            
            if z_score > self.SPIKE_THRESHOLD:
                patterns.append(SignalPattern(
                    timestamp=readings[i].timestamp,
                    pattern_type=PatternType.SPIKE,
                    channel_id=readings[i].channel_id,
                    start_index=max(0, i - 1),
                    end_index=min(len(readings) - 1, i + 1),
                    duration_ms=1000 / self.sample_rate_hz,
                    amplitude=val - mean_val,
                    confidence=min(1.0, abs(z_score) / 5.0),
                    baseline=mean_val,
                    peak_value=val,
                    metadata={"z_score": z_score},
                ))
            
            elif z_score < self.DROP_THRESHOLD:
                patterns.append(SignalPattern(
                    timestamp=readings[i].timestamp,
                    pattern_type=PatternType.DROP,
                    channel_id=readings[i].channel_id,
                    start_index=max(0, i - 1),
                    end_index=min(len(readings) - 1, i + 1),
                    duration_ms=1000 / self.sample_rate_hz,
                    amplitude=val - mean_val,
                    confidence=min(1.0, abs(z_score) / 5.0),
                    baseline=mean_val,
                    peak_value=val,
                    metadata={"z_score": z_score},
                ))
        
        return patterns
    
    def _detect_oscillations(
        self,
        readings: List[FCIReading],
        values: List[float],
    ) -> List[SignalPattern]:
        """Detect oscillation patterns using zero-crossing analysis."""
        if len(values) < 20:
            return []
        
        patterns = []
        
        # Detrend (remove mean)
        mean_val = sum(values) / len(values)
        detrended = [v - mean_val for v in values]
        
        # Find zero crossings
        crossings = []
        for i in range(1, len(detrended)):
            if detrended[i-1] * detrended[i] < 0:
                crossings.append(i)
        
        # Analyze crossing intervals
        if len(crossings) >= self.OSCILLATION_MIN_PERIODS * 2:
            intervals = [crossings[i+1] - crossings[i] for i in range(len(crossings)-1)]
            avg_interval = sum(intervals) / len(intervals)
            
            # Check for regularity
            interval_variance = sum((i - avg_interval) ** 2 for i in intervals) / len(intervals)
            regularity = 1.0 - min(1.0, (interval_variance ** 0.5) / avg_interval) if avg_interval > 0 else 0
            
            if regularity > 0.6:
                # Calculate frequency
                period_samples = avg_interval * 2  # Full period is 2 half-periods
                frequency = self.sample_rate_hz / period_samples if period_samples > 0 else 0
                
                # Calculate amplitude
                amplitude = max(values) - min(values)
                
                patterns.append(SignalPattern(
                    timestamp=readings[crossings[0]].timestamp,
                    pattern_type=PatternType.OSCILLATION,
                    channel_id=readings[0].channel_id,
                    start_index=crossings[0],
                    end_index=crossings[-1],
                    duration_ms=(crossings[-1] - crossings[0]) * 1000 / self.sample_rate_hz,
                    amplitude=amplitude,
                    frequency_hz=frequency,
                    confidence=regularity,
                    baseline=mean_val,
                    peak_value=max(values),
                    metadata={"crossings": len(crossings), "regularity": regularity},
                ))
        
        return patterns
    
    def _detect_trends(
        self,
        readings: List[FCIReading],
        values: List[float],
    ) -> List[SignalPattern]:
        """Detect ramp and decay patterns using linear regression."""
        if len(values) < 10:
            return []
        
        patterns = []
        
        # Simple linear regression
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        
        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator > 0 else 0
        
        # Check for significant trend
        value_range = max(values) - min(values) if values else 0
        trend_magnitude = abs(slope * n)
        
        if value_range > 0 and trend_magnitude / value_range > 0.3:
            pattern_type = PatternType.RAMP if slope > 0 else PatternType.DECAY
            
            patterns.append(SignalPattern(
                timestamp=readings[0].timestamp,
                pattern_type=pattern_type,
                channel_id=readings[0].channel_id,
                start_index=0,
                end_index=n - 1,
                duration_ms=n * 1000 / self.sample_rate_hz,
                amplitude=trend_magnitude,
                confidence=min(1.0, trend_magnitude / value_range),
                baseline=values[0],
                peak_value=values[-1] if slope > 0 else values[0],
                metadata={"slope": slope, "trend_magnitude": trend_magnitude},
            ))
        
        return patterns
    
    def _detect_bursts(
        self,
        readings: List[FCIReading],
        values: List[float],
        mean_val: float,
        std_val: float,
    ) -> List[SignalPattern]:
        """Detect burst patterns (multiple rapid spikes)."""
        patterns = []
        
        # Find all spikes
        spike_indices = []
        for i, val in enumerate(values):
            z_score = (val - mean_val) / std_val if std_val > 0 else 0
            if z_score > self.SPIKE_THRESHOLD:
                spike_indices.append(i)
        
        if len(spike_indices) < self.BURST_MIN_SPIKES:
            return patterns
        
        # Group spikes into bursts
        max_gap = self.BURST_MAX_INTERVAL_MS * self.sample_rate_hz / 1000
        
        bursts = []
        current_burst = [spike_indices[0]]
        
        for i in range(1, len(spike_indices)):
            if spike_indices[i] - spike_indices[i-1] <= max_gap:
                current_burst.append(spike_indices[i])
            else:
                if len(current_burst) >= self.BURST_MIN_SPIKES:
                    bursts.append(current_burst)
                current_burst = [spike_indices[i]]
        
        if len(current_burst) >= self.BURST_MIN_SPIKES:
            bursts.append(current_burst)
        
        # Create patterns for bursts
        for burst in bursts:
            burst_values = [values[i] for i in burst]
            patterns.append(SignalPattern(
                timestamp=readings[burst[0]].timestamp,
                pattern_type=PatternType.BURST,
                channel_id=readings[0].channel_id,
                start_index=burst[0],
                end_index=burst[-1],
                duration_ms=(burst[-1] - burst[0]) * 1000 / self.sample_rate_hz,
                amplitude=max(burst_values) - mean_val,
                confidence=min(1.0, len(burst) / 10.0),
                baseline=mean_val,
                peak_value=max(burst_values),
                metadata={"spike_count": len(burst)},
            ))
        
        return patterns
    
    def detect_synchronized(
        self,
        channel_readings: Dict[int, List[FCIReading]],
    ) -> List[SignalPattern]:
        """Detect synchronized patterns across multiple channels."""
        patterns = []
        
        if len(channel_readings) < 2:
            return patterns
        
        channel_ids = list(channel_readings.keys())
        
        for i, ch1 in enumerate(channel_ids):
            for ch2 in channel_ids[i+1:]:
                readings1 = channel_readings[ch1]
                readings2 = channel_readings[ch2]
                
                if len(readings1) != len(readings2) or len(readings1) < 10:
                    continue
                
                values1 = [r.normalized_value for r in readings1]
                values2 = [r.normalized_value for r in readings2]
                
                # Calculate correlation
                correlation = self._pearson_correlation(values1, values2)
                
                if abs(correlation) >= self.SYNC_CORRELATION_MIN:
                    patterns.append(SignalPattern(
                        timestamp=readings1[0].timestamp,
                        pattern_type=PatternType.SYNCHRONIZED,
                        channel_id=ch1,
                        start_index=0,
                        end_index=len(readings1) - 1,
                        duration_ms=len(readings1) * 1000 / self.sample_rate_hz,
                        amplitude=0,
                        confidence=abs(correlation),
                        metadata={
                            "correlated_channel": ch2,
                            "correlation": correlation,
                        },
                    ))
        
        return patterns
    
    def _pearson_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        n = len(x)
        if n == 0:
            return 0.0
        
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        
        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        
        sum_sq_x = sum((v - mean_x) ** 2 for v in x)
        sum_sq_y = sum((v - mean_y) ** 2 for v in y)
        
        denominator = (sum_sq_x * sum_sq_y) ** 0.5
        
        return numerator / denominator if denominator > 0 else 0.0
    
    def get_recent_patterns(self, count: int = 10) -> List[SignalPattern]:
        """Get most recent detected patterns."""
        return self.detected_patterns[-count:]
    
    def clear_patterns(self) -> None:
        """Clear detected patterns."""
        self.detected_patterns = []
