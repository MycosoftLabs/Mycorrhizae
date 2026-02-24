"""
Mycorrhizae Protocol - Semantic Translation Layer

Translates raw bioelectric signal patterns into semantically meaningful
interpretations based on GFST (Global Fungi Symbiosis Theory).

This is what makes the Mycorrhizae Protocol novel - it doesn't just route
sensor data; it interprets biological signals into actionable intelligence.

Physics/Biology Basis:
- Ion channel dynamics (K+, Ca2+, Na+)
- Membrane potential fluctuations
- Chemical signaling pathways
- Mechanical stress responses
- Diurnal rhythm markers

Version: 1.0.0

(c) 2026 Mycosoft Labs
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import math


# ============================================================================
# SEMANTIC CATEGORIES
# ============================================================================

class SemanticCategory(str, Enum):
    """High-level semantic categories for mycelium signals."""
    METABOLIC = "metabolic"
    ENVIRONMENTAL = "environmental"
    COMMUNICATION = "communication"
    DEFENSIVE = "defensive"
    REPRODUCTIVE = "reproductive"
    PREDICTIVE = "predictive"
    ANOMALOUS = "anomalous"


class SemanticConfidence(str, Enum):
    """Confidence levels for semantic interpretations."""
    CERTAIN = "certain"         # >95% confidence
    HIGH = "high"               # 80-95%
    MODERATE = "moderate"       # 60-80%
    LOW = "low"                 # 40-60%
    SPECULATIVE = "speculative" # <40%


class TemporalPhase(str, Enum):
    """Temporal phase of the detected pattern."""
    ONSET = "onset"         # Pattern just started
    SUSTAINED = "sustained" # Pattern ongoing
    PEAK = "peak"           # Pattern at maximum
    DECLINING = "declining" # Pattern reducing
    TERMINATED = "terminated" # Pattern ended


# ============================================================================
# GFST PATTERN SIGNATURES
# ============================================================================

@dataclass
class PatternSignature:
    """GFST-based pattern signature with physical/biological characteristics."""
    name: str
    category: SemanticCategory
    
    # Bioelectric characteristics
    amplitude_range_uv: Tuple[float, float]
    frequency_range_hz: Tuple[float, float]
    typical_duration_s: Tuple[float, float]
    
    # Feature constraints
    min_snr_db: float = 5.0
    min_quality: float = 0.3
    requires_spikes: bool = False
    spike_rate_range_hz: Optional[Tuple[float, float]] = None
    
    # Spectral characteristics
    dominant_band: str = "low"  # ultra_low, low, mid, high
    band_power_ratios: Optional[Dict[str, Tuple[float, float]]] = None
    
    # Environmental correlation
    env_correlation: Optional[Dict[str, str]] = None
    
    # Semantic meaning
    meaning: str = ""
    implications: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)


# GFST Pattern Library - scientifically grounded pattern definitions
GFST_PATTERN_LIBRARY: Dict[str, PatternSignature] = {
    "baseline": PatternSignature(
        name="baseline",
        category=SemanticCategory.METABOLIC,
        amplitude_range_uv=(0.1, 0.3),
        frequency_range_hz=(0.01, 0.5),
        typical_duration_s=(60, float("inf")),
        dominant_band="ultra_low",
        meaning="Normal resting state with minimal activity",
        implications=["System stable", "No stress detected"],
        actions=["Continue monitoring"],
    ),
    
    "active_growth": PatternSignature(
        name="active_growth",
        category=SemanticCategory.METABOLIC,
        amplitude_range_uv=(0.5, 2.0),
        frequency_range_hz=(0.1, 5.0),
        typical_duration_s=(300, 7200),
        min_snr_db=8.0,
        dominant_band="low",
        band_power_ratios={"low": (0.4, 0.7), "mid": (0.2, 0.4)},
        env_correlation={"temperature": "optimal", "humidity": "high"},
        meaning="Active hyphal growth and colonization",
        implications=[
            "Nutrient availability good",
            "Environmental conditions favorable",
            "Network expansion active",
        ],
        actions=[
            "Document growth rate",
            "Monitor nutrient levels",
            "Consider time-lapse imaging",
        ],
    ),
    
    "nutrient_seeking": PatternSignature(
        name="nutrient_seeking",
        category=SemanticCategory.METABOLIC,
        amplitude_range_uv=(0.3, 1.5),
        frequency_range_hz=(0.5, 3.0),
        typical_duration_s=(60, 600),
        min_snr_db=6.0,
        dominant_band="low",
        meaning="Exploratory behavior seeking nutrients",
        implications=[
            "Current substrate partially depleted",
            "Chemotaxis response active",
        ],
        actions=[
            "Consider nutrient supplementation",
            "Monitor substrate moisture",
        ],
    ),
    
    "temperature_stress": PatternSignature(
        name="temperature_stress",
        category=SemanticCategory.ENVIRONMENTAL,
        amplitude_range_uv=(1.0, 5.0),
        frequency_range_hz=(2.0, 15.0),
        typical_duration_s=(30, 3600),
        min_snr_db=10.0,
        dominant_band="mid",
        env_correlation={"temperature": "extreme"},
        meaning="Thermal stress response",
        implications=[
            "Temperature outside optimal range",
            "Potential heat shock protein activation",
            "Risk of growth inhibition",
        ],
        actions=[
            "Adjust ambient temperature",
            "Check heating/cooling systems",
            "Alert operator",
        ],
    ),
    
    "moisture_stress": PatternSignature(
        name="moisture_stress",
        category=SemanticCategory.ENVIRONMENTAL,
        amplitude_range_uv=(0.8, 3.0),
        frequency_range_hz=(1.0, 8.0),
        typical_duration_s=(60, 1800),
        min_snr_db=7.0,
        dominant_band="mid",
        env_correlation={"humidity": "low"},
        meaning="Desiccation stress response",
        implications=[
            "Substrate moisture too low",
            "Risk of hyphal damage",
            "Possible sporulation trigger",
        ],
        actions=[
            "Increase humidity",
            "Mist substrate",
            "Check for substrate shrinkage",
        ],
    ),
    
    "chemical_stress": PatternSignature(
        name="chemical_stress",
        category=SemanticCategory.DEFENSIVE,
        amplitude_range_uv=(2.0, 10.0),
        frequency_range_hz=(5.0, 20.0),
        typical_duration_s=(30, 300),
        min_snr_db=12.0,
        requires_spikes=True,
        spike_rate_range_hz=(0.5, 5.0),
        dominant_band="mid",
        meaning="Response to chemical irritant or toxin",
        implications=[
            "Potential contamination detected",
            "Defensive compound production",
            "Metabolic pathway alteration",
        ],
        actions=[
            "Identify contaminant source",
            "Consider quarantine",
            "Sample for analysis",
        ],
    ),
    
    "network_communication": PatternSignature(
        name="network_communication",
        category=SemanticCategory.COMMUNICATION,
        amplitude_range_uv=(0.5, 3.0),
        frequency_range_hz=(0.2, 2.0),
        typical_duration_s=(5, 60),
        min_snr_db=8.0,
        requires_spikes=True,
        spike_rate_range_hz=(0.1, 1.0),
        dominant_band="low",
        meaning="Inter-hyphal signaling detected",
        implications=[
            "Information propagating through network",
            "Potential resource allocation",
            "Coordinated response possible",
        ],
        actions=[
            "Monitor multiple channels",
            "Track signal propagation",
            "Correlate with environmental events",
        ],
    ),
    
    "action_potential": PatternSignature(
        name="action_potential",
        category=SemanticCategory.COMMUNICATION,
        amplitude_range_uv=(2.0, 50.0),
        frequency_range_hz=(0.5, 5.0),
        typical_duration_s=(0.5, 5.0),
        min_snr_db=15.0,
        requires_spikes=True,
        spike_rate_range_hz=(0.5, 3.0),
        dominant_band="mid",
        meaning="Discrete action potential-like spike",
        implications=[
            "Rapid signal transmission",
            "Ion channel activation",
            "Possible response to acute stimulus",
        ],
        actions=[
            "Record waveform",
            "Correlate with stimuli",
            "Store for pattern learning",
        ],
    ),
    
    "seismic_precursor": PatternSignature(
        name="seismic_precursor",
        category=SemanticCategory.PREDICTIVE,
        amplitude_range_uv=(0.1, 1.0),
        frequency_range_hz=(0.001, 0.1),
        typical_duration_s=(3600, 86400),
        min_snr_db=5.0,
        dominant_band="ultra_low",
        meaning="Potential seismic precursor signal (GFST hypothesis)",
        implications=[
            "Ultra-low frequency oscillation detected",
            "Possible piezoelectric response to tectonic stress",
            "REQUIRES VALIDATION - experimental",
        ],
        actions=[
            "Log for correlation with seismic data",
            "Do not generate public alerts",
            "Archive for GFST research",
        ],
    ),
    
    "circadian_rhythm": PatternSignature(
        name="circadian_rhythm",
        category=SemanticCategory.METABOLIC,
        amplitude_range_uv=(0.2, 0.8),
        frequency_range_hz=(0.00001, 0.0001),  # ~12-24 hour period
        typical_duration_s=(43200, 172800),
        dominant_band="ultra_low",
        meaning="Diurnal metabolic oscillation",
        implications=[
            "Normal circadian activity",
            "Light/temperature entrainment working",
        ],
        actions=[
            "Confirm light cycle",
            "Document pattern for baseline",
        ],
    ),
    
    "sporulation_initiation": PatternSignature(
        name="sporulation_initiation",
        category=SemanticCategory.REPRODUCTIVE,
        amplitude_range_uv=(1.0, 4.0),
        frequency_range_hz=(0.5, 3.0),
        typical_duration_s=(1800, 14400),
        min_snr_db=10.0,
        dominant_band="low",
        env_correlation={"humidity": "cycling", "temperature": "dropping"},
        meaning="Sporulation process beginning",
        implications=[
            "Reproductive phase initiated",
            "Nutrient allocation shifting",
            "End of vegetative growth approaching",
        ],
        actions=[
            "Prepare for spore collection",
            "Document environmental conditions",
            "Consider harvesting if cultivation",
        ],
    ),
    
    "defense_activation": PatternSignature(
        name="defense_activation",
        category=SemanticCategory.DEFENSIVE,
        amplitude_range_uv=(3.0, 15.0),
        frequency_range_hz=(8.0, 30.0),
        typical_duration_s=(10, 300),
        min_snr_db=15.0,
        requires_spikes=True,
        spike_rate_range_hz=(2.0, 10.0),
        dominant_band="high",
        meaning="Acute defensive response",
        implications=[
            "Predator or pathogen contact",
            "Secondary metabolite production",
            "Possible cell wall reinforcement",
        ],
        actions=[
            "Inspect for contamination",
            "Check for insect activity",
            "Sample for metabolite analysis",
        ],
    ),
}


# ============================================================================
# SEMANTIC INTERPRETATION ENGINE
# ============================================================================

@dataclass
class SemanticInterpretation:
    """A semantic interpretation of a detected pattern."""
    pattern_name: str
    category: SemanticCategory
    confidence: SemanticConfidence
    confidence_score: float
    
    meaning: str
    implications: List[str]
    actions: List[str]
    
    phase: TemporalPhase
    duration_so_far_s: float
    estimated_remaining_s: Optional[float]
    
    environmental_context: Dict[str, Any]
    feature_match_scores: Dict[str, float]
    
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_name": self.pattern_name,
            "category": self.category.value,
            "confidence": {
                "level": self.confidence.value,
                "score": self.confidence_score,
            },
            "meaning": self.meaning,
            "implications": self.implications,
            "actions": self.actions,
            "temporal": {
                "phase": self.phase.value,
                "duration_so_far_s": self.duration_so_far_s,
                "estimated_remaining_s": self.estimated_remaining_s,
            },
            "environmental_context": self.environmental_context,
            "feature_match_scores": self.feature_match_scores,
            "timestamp": self.timestamp.isoformat(),
        }


class SemanticTranslator:
    """
    Translates bioelectric signals into semantic interpretations.
    
    This is the core innovation of the Mycorrhizae Protocol.
    """
    
    def __init__(self, pattern_library: Dict[str, PatternSignature] = None):
        self.pattern_library = pattern_library or GFST_PATTERN_LIBRARY
        
        # Active pattern tracking
        self._active_patterns: Dict[str, Dict[str, Any]] = {}
        
        # Interpretation history for temporal analysis
        self._history: List[SemanticInterpretation] = []
        self._max_history = 1000
    
    def translate(
        self,
        pattern_name: str,
        features: Dict[str, Any],
        environment: Dict[str, Any],
        pattern_start_time: Optional[datetime] = None,
    ) -> SemanticInterpretation:
        """
        Translate a detected pattern into semantic meaning.
        
        Args:
            pattern_name: Name of detected pattern
            features: Extracted signal features (amplitude, frequency, etc.)
            environment: Environmental sensor data
            pattern_start_time: When pattern was first detected
            
        Returns:
            Semantic interpretation with meaning, implications, and actions
        """
        signature = self.pattern_library.get(pattern_name)
        
        if not signature:
            # Unknown pattern - return anomalous interpretation
            return self._create_anomalous_interpretation(pattern_name, features, environment)
        
        # Calculate feature match scores
        match_scores = self._calculate_match_scores(signature, features)
        
        # Calculate overall confidence
        confidence_score = self._calculate_confidence(match_scores, features, environment, signature)
        confidence_level = self._score_to_confidence_level(confidence_score)
        
        # Determine temporal phase
        now = datetime.now(timezone.utc)
        duration_s = 0.0
        if pattern_start_time:
            duration_s = (now - pattern_start_time).total_seconds()
        
        phase = self._determine_phase(pattern_name, duration_s, features, signature)
        
        # Estimate remaining duration
        remaining_s = self._estimate_remaining_duration(signature, duration_s, phase)
        
        # Build environmental context
        env_context = self._build_environmental_context(environment, signature)
        
        # Create interpretation
        interpretation = SemanticInterpretation(
            pattern_name=pattern_name,
            category=signature.category,
            confidence=confidence_level,
            confidence_score=confidence_score,
            meaning=signature.meaning,
            implications=self._filter_implications(signature.implications, confidence_score),
            actions=self._filter_actions(signature.actions, confidence_score, phase),
            phase=phase,
            duration_so_far_s=duration_s,
            estimated_remaining_s=remaining_s,
            environmental_context=env_context,
            feature_match_scores=match_scores,
        )
        
        # Track active patterns
        self._update_active_patterns(pattern_name, interpretation)
        
        # Add to history
        self._add_to_history(interpretation)
        
        return interpretation
    
    def _calculate_match_scores(
        self,
        signature: PatternSignature,
        features: Dict[str, Any],
    ) -> Dict[str, float]:
        """Calculate how well features match the signature."""
        scores = {}
        
        # Amplitude match
        amp = features.get("amplitude_uv", 0)
        amp_min, amp_max = signature.amplitude_range_uv
        if amp_min <= amp <= amp_max:
            # Perfect match
            scores["amplitude"] = 1.0
        elif amp < amp_min:
            scores["amplitude"] = max(0, amp / amp_min)
        else:
            scores["amplitude"] = max(0, 1 - (amp - amp_max) / amp_max)
        
        # Frequency match
        freq = features.get("dominant_freq_hz", 0)
        freq_min, freq_max = signature.frequency_range_hz
        if freq_min <= freq <= freq_max:
            scores["frequency"] = 1.0
        elif freq < freq_min:
            scores["frequency"] = max(0, freq / freq_min) if freq_min > 0 else 0.5
        else:
            scores["frequency"] = max(0, 1 - (freq - freq_max) / freq_max)
        
        # SNR match
        snr = features.get("snr_db", 0)
        if snr >= signature.min_snr_db:
            scores["snr"] = 1.0
        else:
            scores["snr"] = max(0, snr / signature.min_snr_db)
        
        # Quality match
        quality = features.get("quality_score", 0)
        if quality >= signature.min_quality:
            scores["quality"] = 1.0
        else:
            scores["quality"] = quality / signature.min_quality
        
        # Spike detection match
        if signature.requires_spikes:
            spike_count = features.get("spike_count", 0)
            spike_rate = features.get("spike_rate_hz", 0)
            
            if spike_count > 0:
                scores["spikes_present"] = 1.0
                
                if signature.spike_rate_range_hz:
                    rate_min, rate_max = signature.spike_rate_range_hz
                    if rate_min <= spike_rate <= rate_max:
                        scores["spike_rate"] = 1.0
                    else:
                        scores["spike_rate"] = 0.5
                else:
                    scores["spike_rate"] = 0.8
            else:
                scores["spikes_present"] = 0.0
                scores["spike_rate"] = 0.0
        
        # Band power match
        if signature.band_power_ratios:
            band_powers = features.get("band_powers", {})
            total_power = features.get("total_power", 1)
            
            for band, (expected_min, expected_max) in signature.band_power_ratios.items():
                band_power = band_powers.get(band, 0)
                ratio = band_power / total_power if total_power > 0 else 0
                
                if expected_min <= ratio <= expected_max:
                    scores[f"band_{band}"] = 1.0
                else:
                    distance = min(abs(ratio - expected_min), abs(ratio - expected_max))
                    scores[f"band_{band}"] = max(0, 1 - distance * 2)
        
        return scores
    
    def _calculate_confidence(
        self,
        match_scores: Dict[str, float],
        features: Dict[str, Any],
        environment: Dict[str, Any],
        signature: PatternSignature,
    ) -> float:
        """Calculate overall confidence score (0-1)."""
        if not match_scores:
            return 0.0
        
        # Weight different scores
        weights = {
            "amplitude": 0.25,
            "frequency": 0.25,
            "snr": 0.15,
            "quality": 0.1,
            "spikes_present": 0.15,
            "spike_rate": 0.1,
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for key, score in match_scores.items():
            weight = weights.get(key, 0.05)
            weighted_sum += score * weight
            total_weight += weight
        
        base_confidence = weighted_sum / total_weight if total_weight > 0 else 0
        
        # Environmental correlation bonus
        if signature.env_correlation:
            env_bonus = self._check_environmental_correlation(environment, signature.env_correlation)
            base_confidence = min(1.0, base_confidence + env_bonus * 0.1)
        
        return base_confidence
    
    def _check_environmental_correlation(
        self,
        environment: Dict[str, Any],
        expected: Dict[str, str],
    ) -> float:
        """Check how well environment matches expected correlations."""
        matches = 0
        total = len(expected)
        
        if total == 0:
            return 0.5
        
        for param, expected_state in expected.items():
            value = environment.get(f"{param}_c", environment.get(param))
            if value is None:
                continue
            
            if param == "temperature":
                if expected_state == "extreme":
                    matches += 1 if (value < 10 or value > 35) else 0
                elif expected_state == "optimal":
                    matches += 1 if 20 <= value <= 30 else 0.5
                elif expected_state == "dropping":
                    # Would need temporal data
                    matches += 0.5
            elif param == "humidity":
                if expected_state == "high":
                    matches += 1 if value > 80 else 0
                elif expected_state == "low":
                    matches += 1 if value < 40 else 0
                elif expected_state == "cycling":
                    matches += 0.5  # Would need temporal data
            else:
                matches += 0.5  # Unknown parameter
        
        return matches / total
    
    def _score_to_confidence_level(self, score: float) -> SemanticConfidence:
        """Convert numeric score to confidence level."""
        if score >= 0.95:
            return SemanticConfidence.CERTAIN
        elif score >= 0.80:
            return SemanticConfidence.HIGH
        elif score >= 0.60:
            return SemanticConfidence.MODERATE
        elif score >= 0.40:
            return SemanticConfidence.LOW
        else:
            return SemanticConfidence.SPECULATIVE
    
    def _determine_phase(
        self,
        pattern_name: str,
        duration_s: float,
        features: Dict[str, Any],
        signature: PatternSignature,
    ) -> TemporalPhase:
        """Determine temporal phase of the pattern."""
        typ_min, typ_max = signature.typical_duration_s
        
        # Check if pattern was previously active
        if pattern_name in self._active_patterns:
            prev = self._active_patterns[pattern_name]
            prev_amplitude = prev.get("last_amplitude", 0)
            curr_amplitude = features.get("amplitude_uv", 0)
            
            # Amplitude trending analysis
            if curr_amplitude > prev_amplitude * 1.2:
                return TemporalPhase.ONSET
            elif curr_amplitude < prev_amplitude * 0.8:
                return TemporalPhase.DECLINING
        
        if duration_s < typ_min * 0.2:
            return TemporalPhase.ONSET
        elif duration_s < typ_min * 0.8:
            return TemporalPhase.SUSTAINED
        elif duration_s < typ_max * 0.8:
            return TemporalPhase.PEAK
        else:
            return TemporalPhase.DECLINING
    
    def _estimate_remaining_duration(
        self,
        signature: PatternSignature,
        duration_so_far_s: float,
        phase: TemporalPhase,
    ) -> Optional[float]:
        """Estimate remaining pattern duration."""
        typ_min, typ_max = signature.typical_duration_s
        
        if typ_max == float("inf"):
            return None
        
        if phase == TemporalPhase.DECLINING:
            return typ_min * 0.1  # Nearly done
        elif phase == TemporalPhase.PEAK:
            return (typ_max - duration_so_far_s) * 0.5
        else:
            expected_total = (typ_min + typ_max) / 2
            return max(0, expected_total - duration_so_far_s)
    
    def _filter_implications(
        self,
        implications: List[str],
        confidence: float,
    ) -> List[str]:
        """Filter implications based on confidence."""
        if confidence >= 0.8:
            return implications
        elif confidence >= 0.6:
            return implications[:max(1, len(implications) - 1)]
        else:
            return implications[:1] if implications else []
    
    def _filter_actions(
        self,
        actions: List[str],
        confidence: float,
        phase: TemporalPhase,
    ) -> List[str]:
        """Filter actions based on confidence and phase."""
        result = []
        
        for action in actions:
            # Some actions require higher confidence
            if "alert" in action.lower() and confidence < 0.7:
                continue
            if "quarantine" in action.lower() and confidence < 0.85:
                continue
            
            # Some actions only make sense at certain phases
            if "prepare" in action.lower() and phase not in [TemporalPhase.ONSET, TemporalPhase.SUSTAINED]:
                continue
            
            result.append(action)
        
        return result
    
    def _build_environmental_context(
        self,
        environment: Dict[str, Any],
        signature: PatternSignature,
    ) -> Dict[str, Any]:
        """Build environmental context for interpretation."""
        context = {}
        
        # Include relevant environmental data
        if environment.get("temperature_c") is not None:
            temp = environment["temperature_c"]
            context["temperature"] = {
                "value": temp,
                "unit": "C",
                "assessment": "optimal" if 20 <= temp <= 30 else ("cold" if temp < 20 else "warm"),
            }
        
        if environment.get("humidity_pct") is not None:
            hum = environment["humidity_pct"]
            context["humidity"] = {
                "value": hum,
                "unit": "%",
                "assessment": "high" if hum > 80 else ("low" if hum < 40 else "moderate"),
            }
        
        if environment.get("voc_index") is not None:
            voc = environment["voc_index"]
            context["air_quality"] = {
                "value": voc,
                "assessment": "good" if voc < 100 else ("moderate" if voc < 200 else "poor"),
            }
        
        # Check correlation with expected
        if signature.env_correlation:
            context["correlation_check"] = {}
            for param, expected in signature.env_correlation.items():
                ctx_param = context.get(param, {})
                actual = ctx_param.get("assessment", "unknown")
                context["correlation_check"][param] = {
                    "expected": expected,
                    "actual": actual,
                    "matches": expected.lower() in actual.lower() if actual != "unknown" else None,
                }
        
        return context
    
    def _create_anomalous_interpretation(
        self,
        pattern_name: str,
        features: Dict[str, Any],
        environment: Dict[str, Any],
    ) -> SemanticInterpretation:
        """Create interpretation for unknown/anomalous pattern."""
        return SemanticInterpretation(
            pattern_name=pattern_name,
            category=SemanticCategory.ANOMALOUS,
            confidence=SemanticConfidence.SPECULATIVE,
            confidence_score=0.2,
            meaning="Unknown pattern detected - requires analysis",
            implications=[
                "Pattern not in GFST library",
                "May represent new phenomenon or noise",
            ],
            actions=[
                "Log for manual review",
                "Check sensor calibration",
                "Consider adding to pattern library if persistent",
            ],
            phase=TemporalPhase.ONSET,
            duration_so_far_s=0,
            estimated_remaining_s=None,
            environmental_context={
                "temperature_c": environment.get("temperature_c"),
                "humidity_pct": environment.get("humidity_pct"),
            },
            feature_match_scores={},
        )
    
    def _update_active_patterns(
        self,
        pattern_name: str,
        interpretation: SemanticInterpretation,
    ) -> None:
        """Update tracking of active patterns."""
        if interpretation.phase == TemporalPhase.TERMINATED:
            self._active_patterns.pop(pattern_name, None)
        else:
            self._active_patterns[pattern_name] = {
                "started": datetime.now(timezone.utc) - timedelta(seconds=interpretation.duration_so_far_s),
                "last_seen": datetime.now(timezone.utc),
                "last_amplitude": interpretation.feature_match_scores.get("amplitude", 0),
                "phase": interpretation.phase,
            }
    
    def _add_to_history(self, interpretation: SemanticInterpretation) -> None:
        """Add interpretation to history."""
        self._history.append(interpretation)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
    
    def get_active_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Get currently active patterns."""
        return dict(self._active_patterns)
    
    def get_recent_history(self, count: int = 10) -> List[SemanticInterpretation]:
        """Get recent interpretation history."""
        return self._history[-count:]


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

# Global translator instance
_default_translator: Optional[SemanticTranslator] = None


def get_translator() -> SemanticTranslator:
    """Get the default semantic translator instance."""
    global _default_translator
    if _default_translator is None:
        _default_translator = SemanticTranslator()
    return _default_translator


def translate_pattern(
    pattern_name: str,
    features: Dict[str, Any],
    environment: Dict[str, Any] = None,
    pattern_start_time: Optional[datetime] = None,
) -> SemanticInterpretation:
    """
    Convenience function to translate a pattern.
    
    Usage:
        interpretation = translate_pattern(
            "active_growth",
            {"amplitude_uv": 1.2, "dominant_freq_hz": 0.8, "snr_db": 15},
            {"temperature_c": 25, "humidity_pct": 85},
        )
    """
    return get_translator().translate(
        pattern_name,
        features,
        environment or {},
        pattern_start_time,
    )
