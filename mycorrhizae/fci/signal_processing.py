"""
FCI Signal Processing - Advanced Bioelectric Signal Analysis

Implements scientific signal processing for mycelium bioelectric signals:
- Digital filtering (Butterworth bandpass, notch)
- FFT spectral analysis
- GFST-based pattern detection
- Spike detection with refractory periods
- Cross-correlation for network communication detection

Physics basis:
- Ion channel dynamics: K+ (resting -70mV), Ca2+ (action potentials), Na+ (rapid depolarization)
- Membrane time constants: τ = R*C, typically 10-100ms for fungi
- Signal propagation: 0.5-50 mm/min in mycelial networks

Biology basis:
- Mycorrhizal network signaling (Simard 2018)
- Fungal action potential-like spikes (Olsson & Hansson 1995)
- Mycelium as computational substrate (Adamatzky 2018)

Probe designs supported (Mycosoft FCI probes):
- Type A: Copper-steel differential with agar interface
- Type B: Silver/Silver-chloride reference electrode
- Type C: Platinum-iridium high-precision
- Type D: Carbon fiber for minimal interference

(c) 2026 Mycosoft Labs
"""

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import numpy as np
from scipy import signal as sp_signal
from scipy.fft import fft, fftfreq


# ============================================================================
# ELECTRODE AND PROBE CONFIGURATION
# ============================================================================

class ElectrodeMaterial(str, Enum):
    """Electrode materials tested in Mycosoft FCI probes."""
    COPPER = "copper"                   # Good conductivity, affordable
    STEEL_HARDENED = "steel_hardened"   # Durable, corrosion resistant
    SILVER = "silver"                   # Low noise, Ag/AgCl reference
    SILVER_CHLORIDE = "silver_chloride" # Reference electrode standard
    PLATINUM = "platinum"               # High precision, inert
    IRIDIUM = "iridium"                 # Extremely inert, long-term
    PLATINUM_IRIDIUM = "platinum_iridium"  # Best combination
    CARBON_FIBER = "carbon_fiber"       # Minimal interference, flexible
    GOLD = "gold"                       # Biocompatible, stable
    PEDOT_PSS = "pedot_pss"            # Conducting polymer, conformal


class ProbeType(str, Enum):
    """FCI probe types built by Mycosoft."""
    TYPE_A = "type_a"  # Copper-steel differential with agar interface
    TYPE_B = "type_b"  # Silver/AgCl reference for low-noise
    TYPE_C = "type_c"  # Platinum-iridium high-precision
    TYPE_D = "type_d"  # Carbon fiber minimal interference
    TYPE_E = "type_e"  # Multi-electrode array (MEA)


@dataclass
class ElectrodeConfig:
    """Configuration for a single electrode."""
    material: ElectrodeMaterial
    diameter_mm: float = 0.5
    length_mm: float = 10.0
    spacing_mm: float = 5.0  # Distance to paired electrode
    impedance_typical_ohms: float = 10000.0
    noise_floor_uv: float = 1.0
    
    # Agar interface (for mycelium interaction incentive)
    agar_interface: bool = False
    agar_thickness_mm: float = 2.0
    agar_concentration_pct: float = 2.0  # Typical 1.5-3%


@dataclass 
class ProbeConfig:
    """Configuration for an FCI probe assembly."""
    probe_type: ProbeType
    name: str
    electrodes: List[ElectrodeConfig] = field(default_factory=list)
    
    # Filtering (based on EEG/ECG/EMG standards)
    filter_type: str = "bandpass"  # "bandpass", "highpass", "lowpass"
    highpass_hz: float = 0.1       # DC removal
    lowpass_hz: float = 50.0       # Anti-aliasing, 50/60Hz removal
    notch_hz: Optional[float] = 50.0  # Power line interference
    
    # Amplification
    gain: float = 1000.0           # Instrumentation amp gain
    
    # Sampling
    sample_rate_hz: float = 256.0  # Nyquist-compliant
    adc_bits: int = 16             # Resolution
    
    # Calibration
    calibration_date: Optional[datetime] = None
    baseline_offset_uv: float = 0.0
    scale_factor: float = 1.0


# Standard probe configurations
PROBE_CONFIGS = {
    ProbeType.TYPE_A: ProbeConfig(
        probe_type=ProbeType.TYPE_A,
        name="Copper-Steel Differential with Agar",
        electrodes=[
            ElectrodeConfig(ElectrodeMaterial.COPPER, agar_interface=True),
            ElectrodeConfig(ElectrodeMaterial.STEEL_HARDENED, agar_interface=True),
        ],
        highpass_hz=0.1,
        lowpass_hz=35.0,
        notch_hz=50.0,
    ),
    ProbeType.TYPE_B: ProbeConfig(
        probe_type=ProbeType.TYPE_B,
        name="Silver/AgCl Reference Electrode",
        electrodes=[
            ElectrodeConfig(ElectrodeMaterial.SILVER, noise_floor_uv=0.5),
            ElectrodeConfig(ElectrodeMaterial.SILVER_CHLORIDE, noise_floor_uv=0.3),
        ],
        highpass_hz=0.05,
        lowpass_hz=40.0,
        notch_hz=50.0,
    ),
    ProbeType.TYPE_C: ProbeConfig(
        probe_type=ProbeType.TYPE_C,
        name="Platinum-Iridium High Precision",
        electrodes=[
            ElectrodeConfig(ElectrodeMaterial.PLATINUM_IRIDIUM, noise_floor_uv=0.2),
            ElectrodeConfig(ElectrodeMaterial.PLATINUM_IRIDIUM, noise_floor_uv=0.2),
        ],
        highpass_hz=0.01,
        lowpass_hz=100.0,
        notch_hz=None,  # Low noise, no notch needed
    ),
    ProbeType.TYPE_D: ProbeConfig(
        probe_type=ProbeType.TYPE_D,
        name="Carbon Fiber Minimal Interference",
        electrodes=[
            ElectrodeConfig(ElectrodeMaterial.CARBON_FIBER, noise_floor_uv=0.8),
        ],
        highpass_hz=0.1,
        lowpass_hz=30.0,
    ),
}


# ============================================================================
# BIOLOGICAL SIGNAL PATTERNS (GFST-based)
# ============================================================================

class BiologicalPattern(str, Enum):
    """Biological signal patterns based on GFST research."""
    BASELINE = "baseline"                 # Resting electrical activity
    GROWTH = "growth"                     # Active hyphal extension
    STRESS = "stress"                     # Environmental stress response
    NUTRIENT_SEEKING = "nutrient_seeking" # Chemotropic navigation
    COMMUNICATION = "communication"       # Inter-network signaling
    SEISMIC_PRECURSOR = "seismic_precursor"  # M-Wave earthquake precursor
    ACTION_POTENTIAL = "action_potential" # Spike-like event
    DEFENSE = "defense"                   # Response to pathogens/predators
    SYMBIOTIC = "symbiotic"              # Plant-fungal exchange
    CIRCADIAN = "circadian"              # Daily rhythm patterns


@dataclass
class PatternSignature:
    """Signature defining a biological pattern."""
    pattern: BiologicalPattern
    
    # Frequency characteristics (Hz)
    freq_min: float
    freq_max: float
    
    # Amplitude characteristics (µV)
    amp_min: float
    amp_max: float
    
    # Optional frequency
    freq_dominant: Optional[float] = None
    
    # Temporal characteristics
    duration_min_ms: float = 0
    duration_max_ms: float = float('inf')
    
    # Waveform characteristics
    waveform: str = "any"  # "periodic", "aperiodic", "spike", "oscillation"
    
    # Confidence threshold
    min_confidence: float = 0.6


# GFST pattern signatures based on research
GFST_PATTERNS = [
    PatternSignature(
        pattern=BiologicalPattern.BASELINE,
        freq_min=0.0, freq_max=0.5,
        amp_min=0.0, amp_max=0.3,
        waveform="aperiodic",
    ),
    PatternSignature(
        pattern=BiologicalPattern.GROWTH,
        freq_min=0.1, freq_max=5.0,
        freq_dominant=1.0,
        amp_min=0.5, amp_max=2.0,
        waveform="periodic",
    ),
    PatternSignature(
        pattern=BiologicalPattern.STRESS,
        freq_min=5.0, freq_max=20.0,
        amp_min=1.0, amp_max=10.0,
        waveform="aperiodic",
    ),
    PatternSignature(
        pattern=BiologicalPattern.NUTRIENT_SEEKING,
        freq_min=0.5, freq_max=3.0,
        amp_min=0.3, amp_max=1.5,
        duration_min_ms=5000,
        waveform="oscillation",
    ),
    PatternSignature(
        pattern=BiologicalPattern.COMMUNICATION,
        freq_min=1.0, freq_max=10.0,
        amp_min=0.5, amp_max=5.0,
        waveform="periodic",
    ),
    PatternSignature(
        pattern=BiologicalPattern.SEISMIC_PRECURSOR,
        freq_min=0.01, freq_max=0.1,
        amp_min=0.1, amp_max=1.0,
        duration_min_ms=3600000,  # 1 hour minimum
        waveform="aperiodic",
    ),
    PatternSignature(
        pattern=BiologicalPattern.ACTION_POTENTIAL,
        freq_min=0.0, freq_max=50.0,
        amp_min=2.0, amp_max=100.0,
        duration_min_ms=5, duration_max_ms=100,
        waveform="spike",
    ),
]


# ============================================================================
# SIGNAL PROCESSING PIPELINE
# ============================================================================

@dataclass
class ProcessedSignal:
    """Result of signal processing pipeline."""
    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Input metadata
    sample_count: int = 0
    sample_rate_hz: float = 256.0
    duration_ms: float = 0.0
    probe_type: Optional[ProbeType] = None
    
    # Time-domain features
    amplitude_uv: float = 0.0          # Peak-to-peak
    rms_uv: float = 0.0                # RMS value
    mean_uv: float = 0.0               # DC offset
    std_uv: float = 0.0                # Standard deviation
    skewness: float = 0.0              # Asymmetry
    kurtosis: float = 0.0              # Peakedness
    
    # Frequency-domain features
    dominant_freq_hz: float = 0.0      # Dominant frequency
    spectral_centroid_hz: float = 0.0  # Center of mass of spectrum
    spectral_bandwidth_hz: float = 0.0 # Spread of spectrum
    total_power: float = 0.0           # Total spectral power
    
    # Band powers (physiologically relevant)
    power_ultra_low: float = 0.0       # 0.01-0.1 Hz (seismic)
    power_low: float = 0.0             # 0.1-1 Hz (slow metabolic)
    power_mid: float = 0.0             # 1-10 Hz (growth/activity)
    power_high: float = 0.0            # 10-50 Hz (fast activity)
    
    # Quality metrics
    snr_db: float = 0.0                # Signal-to-noise ratio
    quality_score: float = 0.0         # Overall quality (0-1)
    artifact_score: float = 0.0        # Artifact contamination (0-1)
    
    # Pattern detection
    detected_pattern: BiologicalPattern = BiologicalPattern.BASELINE
    pattern_confidence: float = 0.0
    
    # Spike detection
    spike_count: int = 0
    spike_rate_hz: float = 0.0
    
    # Raw data (optional, for debugging)
    raw_samples: Optional[np.ndarray] = None
    filtered_samples: Optional[np.ndarray] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "sample_count": self.sample_count,
            "sample_rate_hz": self.sample_rate_hz,
            "duration_ms": self.duration_ms,
            "probe_type": self.probe_type.value if self.probe_type else None,
            "amplitude_uv": self.amplitude_uv,
            "rms_uv": self.rms_uv,
            "mean_uv": self.mean_uv,
            "std_uv": self.std_uv,
            "dominant_freq_hz": self.dominant_freq_hz,
            "spectral_centroid_hz": self.spectral_centroid_hz,
            "total_power": self.total_power,
            "power_ultra_low": self.power_ultra_low,
            "power_low": self.power_low,
            "power_mid": self.power_mid,
            "power_high": self.power_high,
            "snr_db": self.snr_db,
            "quality_score": self.quality_score,
            "detected_pattern": self.detected_pattern.value,
            "pattern_confidence": self.pattern_confidence,
            "spike_count": self.spike_count,
            "spike_rate_hz": self.spike_rate_hz,
        }


class FCISignalProcessor:
    """
    Advanced signal processor for FCI bioelectric signals.
    
    Implements a full signal processing pipeline:
    1. Preprocessing (DC removal, filtering)
    2. Feature extraction (time and frequency domain)
    3. Pattern detection (GFST-based classification)
    4. Quality assessment
    """
    
    def __init__(
        self,
        sample_rate_hz: float = 256.0,
        probe_config: Optional[ProbeConfig] = None,
    ):
        self.sample_rate_hz = sample_rate_hz
        self.probe_config = probe_config or PROBE_CONFIGS[ProbeType.TYPE_A]
        
        # Running statistics for adaptive processing
        self.running_mean = 0.0
        self.running_std = 1.0
        self.total_samples = 0
        
        # Spike detection state
        self.last_spike_time = 0.0
        self.refractory_period_ms = 50.0  # Minimum time between spikes
        
        # Initialize filters
        self._init_filters()
    
    def _init_filters(self):
        """Initialize digital filter coefficients."""
        fs = self.sample_rate_hz
        nyq = fs / 2
        
        # Bandpass filter (Butterworth)
        low = self.probe_config.highpass_hz / nyq
        high = min(self.probe_config.lowpass_hz / nyq, 0.99)
        
        if low > 0 and high < 1:
            self.bp_b, self.bp_a = sp_signal.butter(4, [low, high], btype='band')
        else:
            self.bp_b, self.bp_a = np.array([1.0]), np.array([1.0])
        
        # Notch filter (if configured)
        if self.probe_config.notch_hz:
            notch_freq = self.probe_config.notch_hz / nyq
            if 0 < notch_freq < 1:
                self.notch_b, self.notch_a = sp_signal.iirnotch(
                    notch_freq, Q=30.0
                )
            else:
                self.notch_b, self.notch_a = np.array([1.0]), np.array([1.0])
        else:
            self.notch_b, self.notch_a = np.array([1.0]), np.array([1.0])
    
    def process(
        self,
        samples: np.ndarray,
        include_raw: bool = False,
    ) -> ProcessedSignal:
        """
        Process a buffer of samples through the full pipeline.
        
        Args:
            samples: Raw ADC samples (microvolts)
            include_raw: Include raw/filtered data in result
            
        Returns:
            ProcessedSignal with extracted features
        """
        samples = np.asarray(samples, dtype=np.float64)
        n_samples = len(samples)
        duration_ms = (n_samples / self.sample_rate_hz) * 1000
        
        result = ProcessedSignal(
            sample_count=n_samples,
            sample_rate_hz=self.sample_rate_hz,
            duration_ms=duration_ms,
            probe_type=self.probe_config.probe_type,
        )
        
        if n_samples < 10:
            return result
        
        # 1. Preprocessing - Apply filters
        filtered = self._apply_filters(samples)
        
        # 2. Time-domain features
        self._extract_time_features(filtered, result)
        
        # 3. Frequency-domain features
        self._extract_freq_features(filtered, result)
        
        # 4. Spike detection
        self._detect_spikes(filtered, result)
        
        # 5. Pattern detection
        self._detect_pattern(result)
        
        # 6. Quality assessment
        self._assess_quality(samples, filtered, result)
        
        # 7. Update running statistics
        self._update_running_stats(filtered)
        
        # Include raw data if requested
        if include_raw:
            result.raw_samples = samples
            result.filtered_samples = filtered
        
        return result
    
    def _apply_filters(self, samples: np.ndarray) -> np.ndarray:
        """Apply bandpass and notch filters."""
        # Remove DC offset first
        samples = samples - np.mean(samples)
        
        # Apply bandpass filter
        filtered = sp_signal.filtfilt(self.bp_b, self.bp_a, samples)
        
        # Apply notch filter
        filtered = sp_signal.filtfilt(self.notch_b, self.notch_a, filtered)
        
        return filtered
    
    def _extract_time_features(
        self,
        samples: np.ndarray,
        result: ProcessedSignal,
    ):
        """Extract time-domain features."""
        result.mean_uv = float(np.mean(samples))
        result.std_uv = float(np.std(samples))
        result.rms_uv = float(np.sqrt(np.mean(samples**2)))
        result.amplitude_uv = float(np.max(samples) - np.min(samples))
        
        # Higher-order statistics
        if result.std_uv > 0:
            normalized = (samples - result.mean_uv) / result.std_uv
            result.skewness = float(np.mean(normalized**3))
            result.kurtosis = float(np.mean(normalized**4) - 3)  # Excess kurtosis
        else:
            result.skewness = 0.0
            result.kurtosis = 0.0
    
    def _extract_freq_features(
        self,
        samples: np.ndarray,
        result: ProcessedSignal,
    ):
        """Extract frequency-domain features using FFT."""
        n = len(samples)
        
        # Apply Hamming window
        windowed = samples * np.hamming(n)
        
        # Compute FFT
        fft_vals = fft(windowed)
        freqs = fftfreq(n, 1 / self.sample_rate_hz)
        
        # Only positive frequencies
        pos_mask = freqs > 0
        pos_freqs = freqs[pos_mask]
        pos_magnitudes = np.abs(fft_vals[pos_mask])
        
        if len(pos_magnitudes) == 0:
            return
        
        # Power spectral density
        psd = pos_magnitudes**2 / n
        
        # Total power
        result.total_power = float(np.sum(psd))
        
        # Dominant frequency
        max_idx = np.argmax(pos_magnitudes)
        result.dominant_freq_hz = float(pos_freqs[max_idx])
        
        # Spectral centroid (center of mass)
        if result.total_power > 0:
            result.spectral_centroid_hz = float(
                np.sum(pos_freqs * psd) / np.sum(psd)
            )
            
            # Spectral bandwidth
            result.spectral_bandwidth_hz = float(np.sqrt(
                np.sum(((pos_freqs - result.spectral_centroid_hz)**2) * psd) / 
                np.sum(psd)
            ))
        
        # Band powers (physiologically relevant)
        result.power_ultra_low = self._band_power(pos_freqs, psd, 0.01, 0.1)
        result.power_low = self._band_power(pos_freqs, psd, 0.1, 1.0)
        result.power_mid = self._band_power(pos_freqs, psd, 1.0, 10.0)
        result.power_high = self._band_power(pos_freqs, psd, 10.0, 50.0)
    
    def _band_power(
        self,
        freqs: np.ndarray,
        psd: np.ndarray,
        low: float,
        high: float,
    ) -> float:
        """Calculate power in a frequency band."""
        mask = (freqs >= low) & (freqs < high)
        return float(np.sum(psd[mask]))
    
    def _detect_spikes(
        self,
        samples: np.ndarray,
        result: ProcessedSignal,
    ):
        """Detect spike events using adaptive threshold."""
        if result.std_uv == 0:
            return
        
        # Z-score threshold for spike detection
        threshold_sigma = 3.0
        threshold = result.mean_uv + threshold_sigma * result.std_uv
        
        # Find threshold crossings
        above_threshold = samples > threshold
        
        # Find spike peaks (local maxima above threshold)
        spike_count = 0
        last_spike_sample = -1000  # Initialize far in the past
        refractory_samples = int(self.refractory_period_ms * self.sample_rate_hz / 1000)
        
        for i in range(1, len(samples) - 1):
            if above_threshold[i]:
                # Check if local maximum
                if samples[i] > samples[i-1] and samples[i] >= samples[i+1]:
                    # Check refractory period
                    if i - last_spike_sample > refractory_samples:
                        spike_count += 1
                        last_spike_sample = i
        
        result.spike_count = spike_count
        result.spike_rate_hz = spike_count / (result.duration_ms / 1000)
    
    def _detect_pattern(self, result: ProcessedSignal):
        """Detect biological pattern based on signal features."""
        best_pattern = BiologicalPattern.BASELINE
        best_confidence = 0.0
        
        for signature in GFST_PATTERNS:
            confidence = self._match_signature(result, signature)
            
            if confidence > best_confidence and confidence >= signature.min_confidence:
                best_confidence = confidence
                best_pattern = signature.pattern
        
        result.detected_pattern = best_pattern
        result.pattern_confidence = best_confidence
    
    def _match_signature(
        self,
        result: ProcessedSignal,
        signature: PatternSignature,
    ) -> float:
        """Calculate confidence of matching a pattern signature."""
        score = 0.0
        weights = 0.0
        
        # Frequency match
        if signature.freq_min <= result.dominant_freq_hz <= signature.freq_max:
            # How close to dominant frequency (if specified)
            if signature.freq_dominant:
                freq_error = abs(result.dominant_freq_hz - signature.freq_dominant)
                freq_range = signature.freq_max - signature.freq_min
                freq_score = 1.0 - min(1.0, freq_error / (freq_range / 2))
            else:
                freq_score = 1.0
            score += freq_score * 0.4
            weights += 0.4
        
        # Amplitude match
        if signature.amp_min <= result.amplitude_uv <= signature.amp_max:
            score += 0.3
            weights += 0.3
        
        # Duration match
        if signature.duration_min_ms <= result.duration_ms <= signature.duration_max_ms:
            score += 0.2
            weights += 0.2
        
        # Waveform match (spike detection for spike patterns)
        if signature.waveform == "spike" and result.spike_count > 0:
            score += 0.1
            weights += 0.1
        elif signature.waveform == "periodic" and result.dominant_freq_hz > 0.1:
            score += 0.1
            weights += 0.1
        
        return score / weights if weights > 0 else 0.0
    
    def _assess_quality(
        self,
        raw: np.ndarray,
        filtered: np.ndarray,
        result: ProcessedSignal,
    ):
        """Assess signal quality."""
        # Estimate noise floor from high-frequency content
        noise_estimate = self.probe_config.electrodes[0].noise_floor_uv if self.probe_config.electrodes else 1.0
        
        # Signal-to-noise ratio
        if noise_estimate > 0:
            result.snr_db = 20 * math.log10(result.rms_uv / noise_estimate) if result.rms_uv > 0 else 0
        
        # Check for saturation (values near ADC limits)
        adc_max = 2**(self.probe_config.adc_bits - 1) - 1
        saturation_threshold = adc_max * 0.9
        saturated_count = np.sum(np.abs(raw) > saturation_threshold * (1/1000))  # Rough estimate
        saturation_rate = saturated_count / len(raw) if len(raw) > 0 else 0
        
        # Artifact score (high if saturation or extreme values)
        result.artifact_score = min(1.0, saturation_rate * 10)
        
        # Overall quality score
        snr_quality = min(1.0, max(0.0, result.snr_db / 20))  # 20 dB = perfect
        result.quality_score = (snr_quality * 0.6 + (1 - result.artifact_score) * 0.4)
    
    def _update_running_stats(self, samples: np.ndarray):
        """Update running mean and std using Welford's algorithm."""
        for x in samples:
            self.total_samples += 1
            delta = x - self.running_mean
            self.running_mean += delta / self.total_samples
            delta2 = x - self.running_mean
            
            if self.total_samples > 1:
                self.running_std = math.sqrt(
                    (self.running_std**2 * (self.total_samples - 2) + delta * delta2) /
                    (self.total_samples - 1)
                )


# ============================================================================
# CROSS-CHANNEL ANALYSIS
# ============================================================================

class NetworkAnalyzer:
    """
    Analyzes signals across multiple FCI channels to detect
    network-level communication patterns.
    """
    
    def __init__(self, sample_rate_hz: float = 256.0):
        self.sample_rate_hz = sample_rate_hz
    
    def cross_correlation(
        self,
        signal1: np.ndarray,
        signal2: np.ndarray,
        max_lag_ms: float = 1000.0,
    ) -> Tuple[np.ndarray, np.ndarray, float, float]:
        """
        Compute cross-correlation between two signals.
        
        Returns:
            lags: Lag values in ms
            correlation: Correlation values
            max_corr: Maximum correlation
            optimal_lag_ms: Lag at maximum correlation
        """
        max_lag_samples = int(max_lag_ms * self.sample_rate_hz / 1000)
        
        # Normalize signals
        s1 = (signal1 - np.mean(signal1)) / (np.std(signal1) + 1e-10)
        s2 = (signal2 - np.mean(signal2)) / (np.std(signal2) + 1e-10)
        
        # Compute cross-correlation
        corr = np.correlate(s1, s2, mode='full')
        corr = corr / len(s1)  # Normalize
        
        # Get relevant portion
        mid = len(corr) // 2
        start = max(0, mid - max_lag_samples)
        end = min(len(corr), mid + max_lag_samples + 1)
        
        corr_segment = corr[start:end]
        lags = np.arange(-(end - mid), mid - start + 1) * (1000 / self.sample_rate_hz)
        
        # Find maximum correlation
        max_idx = np.argmax(np.abs(corr_segment))
        max_corr = float(corr_segment[max_idx])
        optimal_lag_ms = float(lags[max_idx])
        
        return lags, corr_segment, max_corr, optimal_lag_ms
    
    def detect_propagation(
        self,
        channel_signals: Dict[str, np.ndarray],
        electrode_positions_mm: Dict[str, float],
    ) -> Optional[Dict[str, Any]]:
        """
        Detect signal propagation across channels.
        
        Args:
            channel_signals: Dict of channel_id -> signal array
            electrode_positions_mm: Dict of channel_id -> linear position
            
        Returns:
            Dict with propagation velocity and direction
        """
        if len(channel_signals) < 2:
            return None
        
        channel_ids = list(channel_signals.keys())
        correlations = []
        
        for i in range(len(channel_ids) - 1):
            ch1, ch2 = channel_ids[i], channel_ids[i + 1]
            
            _, _, max_corr, lag_ms = self.cross_correlation(
                channel_signals[ch1],
                channel_signals[ch2],
            )
            
            if abs(max_corr) > 0.5:  # Significant correlation
                distance_mm = abs(
                    electrode_positions_mm.get(ch2, 0) -
                    electrode_positions_mm.get(ch1, 0)
                )
                
                if lag_ms != 0:
                    velocity_mm_per_min = (distance_mm / lag_ms) * 60000
                    
                    correlations.append({
                        "channels": (ch1, ch2),
                        "correlation": max_corr,
                        "lag_ms": lag_ms,
                        "velocity_mm_per_min": velocity_mm_per_min,
                    })
        
        if not correlations:
            return None
        
        # Average velocity
        velocities = [c["velocity_mm_per_min"] for c in correlations]
        avg_velocity = sum(velocities) / len(velocities)
        
        return {
            "propagation_detected": True,
            "average_velocity_mm_per_min": avg_velocity,
            "direction": "forward" if avg_velocity > 0 else "backward",
            "channel_correlations": correlations,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
