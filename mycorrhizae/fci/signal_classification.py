"""
FCI Signal Classification - Species Pattern Library

Embeds species-specific electrical spike train patterns from peer-reviewed literature
for real-time classification of fungal signals.

Based on:
- Adamatzky (2022) Royal Society Open Science
- Buffi et al. (2025) iScience  
- Fukasawa et al. (2024) Scientific Reports

This module allows Mycorrhizae Protocol to recognize and classify fungal
electrical patterns against known species profiles.
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import numpy as np


@dataclass
class SpikeTrainPattern:
    """Template for a known spike train pattern."""
    name: str
    species: str
    description: str
    duration_range: Tuple[float, float]  # minutes
    spike_count_range: Tuple[int, int]
    amplitude_range: Tuple[float, float]  # mV
    frequency_range: Tuple[float, float]  # Hz
    characteristics: Dict[str, any]
    reference_doi: str


# ============================================================================
# Species-Specific Pattern Library from Literature
# ============================================================================

SPIKE_TRAIN_PATTERNS = {
    # ========================================================================
    # Schizophyllum commune - Most Complex Patterns
    # ========================================================================
    "schizophyllum_burst_wave": {
        "species": "Schizophyllum commune",
        "description": "Wave packet with increasing then decreasing amplitude and frequency",
        "duration_range": (30, 120),  # minutes
        "spike_count_range": (10, 30),
        "amplitude_range": (0.01, 0.08),  # mV
        "frequency_range": (0.5, 8.0),  # Hz
        "characteristics": {
            "frequency_evolution": "accelerating_then_decelerating",
            "amplitude_evolution": "crescendo_then_diminuendo",
            "complexity": "highest",  # Most complex sentences (Adamatzky 2022)
            "synchronization": True,  # Between fruit bodies
            "typical_sequence": [
                "low_amplitude_start",
                "frequency_increase",
                "amplitude_peak",
                "frequency_decrease",
                "low_amplitude_end"
            ]
        },
        "reference_doi": "10.1098/rsos.211926"
    },
    
    "schizophyllum_fast_spiking": {
        "species": "Schizophyllum commune",
        "description": "Rapid regular spiking - fastest among studied species",
        "duration_range": (10, 60),
        "spike_count_range": (5, 20),
        "amplitude_range": (0.02, 0.05),
        "frequency_range": (0.5, 3.0),
        "characteristics": {
            "avg_interval": 41,  # minutes - shortest ISI
            "regularity": "high",
            "baseline_activity": True
        },
        "reference_doi": "10.1098/rsos.211926"
    },
    
    # ========================================================================
    # Flammulina velutipes - Burst Mode Transitions
    # ========================================================================
    "flammulina_low_freq_oscillation": {
        "species": "Flammulina velutipes",
        "description": "Low frequency irregular oscillation baseline mode",
        "duration_range": (60, 300),
        "spike_count_range": (5, 15),
        "amplitude_range": (0.1, 0.5),
        "frequency_range": (0.001, 0.1),
        "characteristics": {
            "period": 14,  # minutes
            "regularity": "irregular",
            "mode": "baseline"
        },
        "reference_doi": "10.1098/rsos.211926"
    },
    
    "flammulina_high_freq_burst": {
        "species": "Flammulina velutipes",
        "description": "High frequency burst with dramatically increased amplitude",
        "duration_range": (5, 20),
        "spike_count_range": (10, 15),
        "amplitude_range": (1.0, 2.1),  # Can reach 2.1 mV!
        "frequency_range": (0.5, 5.0),
        "characteristics": {
            "period": 2.6,  # minutes - rapid bursts
            "mode": "burst",
            "transition_type": "sudden",  # Rapid switch from low to high freq
            "avg_burst_amplitude": 2.1,  # mV
            "burst_duration": 64  # minutes typical
        },
        "reference_doi": "10.1098/rsos.211926"
    },
    
    # ========================================================================
    # Pleurotus species - Resource Response
    # ========================================================================
    "pleurotus_low_freq": {
        "species": "Pleurotus djamor",
        "description": "Low frequency mode during exploration",
        "duration_range": (60, 240),
        "spike_count_range": (5, 15),
        "amplitude_range": (0.1, 0.5),
        "frequency_range": (0.01, 0.5),
        "characteristics": {
            "period": 14,  # minutes
            "context": "exploration_phase"
        },
        "reference_doi": "10.1038/s41598-018-26007-1"
    },
    
    "pleurotus_high_freq": {
        "species": "Pleurotus djamor",
        "description": "High frequency mode during active response",
        "duration_range": (10, 60),
        "spike_count_range": (8, 20),
        "amplitude_range": (0.3, 2.0),
        "frequency_range": (0.1, 5.0),
        "characteristics": {
            "period": 2.6,  # minutes
            "context": "stimulus_response",
            "triggers": ["fire", "salt", "water", "alcohol", "weight", "wood_contact"]
        },
        "reference_doi": "10.1038/s41598-018-26007-1"
    },
    
    "pleurotus_rhizomorph": {
        "species": "Pleurotus ostreatus",
        "description": "High amplitude spiking in specialized cord structures",
        "duration_range": (60, 300),
        "spike_count_range": (10, 50),
        "amplitude_range": (5, 50),  # mV - very high in cords!
        "frequency_range": (0.5, 5.0),  # Hz
        "characteristics": {
            "structure": "cord_or_rhizomorph",  # NOT regular mycelium
            "amplitude_explanation": "Specialized structures with higher signal"
        },
        "reference_doi": "10.1007/BF01167867"
    },
    
    # ========================================================================
    # Pholiota brunnescens - Week-Long Oscillation (Record!)
    # ========================================================================
    "pholiota_week_cycle": {
        "species": "Pholiota brunnescens",
        "description": "Week-long oscillation - longest period ever recorded in fungi",
        "duration_range": (10080, 10080),  # 7 days exactly
        "spike_count_range": (1, 3),  # Very few spikes per cycle
        "amplitude_range": (0.01, 0.1),
        "frequency_range": (0.00001, 0.0001),  # Ultra-low frequency
        "characteristics": {
            "period": 10080,  # minutes = 7 days
            "phase": "resource_colonization",
            "pacemaker_behavior": True,  # Bait acts as pacemaker
            "causality": "directional_from_bait",
            "unique": "LONGEST_OSCILLATION_KNOWN",
            "onset": "after_60_days",  # Starts ~day 60 of incubation
        },
        "reference_doi": "10.1038/s41598-024-66223-6"
    },
    
    # ========================================================================
    # Fusarium oxysporum - Model Organism
    # ========================================================================
    "fusarium_standard_activity": {
        "species": "Fusarium oxysporum",
        "description": "Standard spike activity with clear STFT signature",
        "duration_range": (30, 180),
        "spike_count_range": (5, 20),
        "amplitude_range": (0.01, 0.2),
        "frequency_range": (1.5, 8.0),  # Biological signature band
        "characteristics": {
            "stft_signature": "1.5_to_8_Hz_emergence",
            "colonization_time": 72,  # hours (3 days typical)
            "psd_increase": 1604,  # percent vs control
            "model_organism": True
        },
        "reference_doi": "10.1016/j.isci.2025.113484"
    },
    
    # ========================================================================
    # Cordyceps militaris - Low Frequency High Amplitude
    # ========================================================================
    "cordyceps_slow_regular": {
        "species": "Cordyceps militaris",
        "description": "Slow regular spiking with high amplitude",
        "duration_range": (120, 480),
        "spike_count_range": (3, 10),
        "amplitude_range": (0.1, 0.4),
        "frequency_range": (0.001, 0.05),
        "characteristics": {
            "avg_interval": 116,  # minutes - slowest among common species
            "regularity": "moderate",
            "context": "entomopathogen_metabolism"
        },
        "reference_doi": "10.1098/rsos.211926"
    },
    
    # ========================================================================
    # Armillaria bulbosa - Cord-Specific High Amplitude
    # ========================================================================
    "armillaria_cord_spiking": {
        "species": "Armillaria bulbosa",
        "description": "Action potential-like spikes in cords triggered by wood",
        "duration_range": (60, 240),
        "spike_count_range": (10, 50),
        "amplitude_range": (5, 50),  # mV - similar to animal sensory systems!
        "frequency_range": (0.5, 5.0),  # Hz
        "characteristics": {
            "structure": "cords_rhizomorphs",
            "trigger": "wood_block_contact",
            "historical_significance": "First observed action potentials in fungi (1995)",
            "amplitude_note": "Unusually high - specialized structures"
        },
        "reference_doi": "10.1007/BF01167867"
    }
}


# ============================================================================
# Pattern Matching and Classification
# ============================================================================

class SignalPatternClassifier:
    """
    Classifies observed fungal electrical signals against known patterns.
    
    Enables real-time species identification and pattern recognition
    based on spike train characteristics.
    """
    
    def __init__(self):
        self.patterns = SPIKE_TRAIN_PATTERNS
        
    def classify_spike_train(
        self,
        spike_count: int,
        duration_minutes: float,
        avg_amplitude_mv: float,
        avg_interval_minutes: float
    ) -> List[Tuple[str, float]]:
        """
        Classify spike train against known patterns.
        
        Returns:
            List of (pattern_name, confidence_score) tuples, sorted by confidence
        """
        matches = []
        
        for pattern_key, pattern in self.patterns.items():
            confidence = self._calculate_match_confidence(
                spike_count,
                duration_minutes,
                avg_amplitude_mv,
                avg_interval_minutes,
                pattern
            )
            
            if confidence > 0.3:  # Threshold for consideration
                matches.append((pattern_key, confidence))
        
        # Sort by confidence
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return matches
    
    def _calculate_match_confidence(
        self,
        spike_count: int,
        duration: float,
        amplitude: float,
        interval: float,
        pattern: Dict
    ) -> float:
        """
        Calculate confidence score for pattern match.
        
        Score components:
        - Duration match: 0-0.25
        - Spike count match: 0-0.25
        - Amplitude match: 0-0.25
        - Interval match: 0-0.25
        Total: 0-1.0
        """
        score = 0.0
        
        # Duration match
        dur_min, dur_max = pattern["duration_range"]
        if dur_min <= duration <= dur_max:
            score += 0.25
        elif dur_min * 0.5 <= duration <= dur_max * 1.5:
            score += 0.15  # Partial credit
        
        # Spike count match
        count_min, count_max = pattern["spike_count_range"]
        if count_min <= spike_count <= count_max:
            score += 0.25
        elif count_min * 0.7 <= spike_count <= count_max * 1.3:
            score += 0.15
        
        # Amplitude match
        amp_min, amp_max = pattern["amplitude_range"]
        if amp_min <= amplitude <= amp_max:
            score += 0.25
        elif amp_min * 0.5 <= amplitude <= amp_max * 2.0:
            score += 0.15
        
        # Frequency/interval match
        freq_min, freq_max = pattern["frequency_range"]
        observed_freq = 1 / (interval * 60) if interval > 0 else 0  # Convert min to Hz
        
        if freq_min <= observed_freq <= freq_max:
            score += 0.25
        elif freq_min * 0.5 <= observed_freq <= freq_max * 2.0:
            score += 0.15
        
        return min(1.0, score)
    
    def identify_species(
        self,
        spike_train_data: Dict
    ) -> Dict[str, float]:
        """
        Identify likely species from spike train data.
        
        Args:
            spike_train_data: Dict with spike_count, duration, avg_amplitude, avg_interval
            
        Returns:
            Dict of {species_name: confidence_score}
        """
        pattern_matches = self.classify_spike_train(
            spike_train_data.get('spike_count', 0),
            spike_train_data.get('duration_minutes', 0),
            spike_train_data.get('avg_amplitude_mv', 0),
            spike_train_data.get('avg_interval_minutes', 0)
        )
        
        # Aggregate by species
        species_scores: Dict[str, float] = {}
        for pattern_key, confidence in pattern_matches:
            species = self.patterns[pattern_key]['species']
            species_scores[species] = max(species_scores.get(species, 0), confidence)
        
        return species_scores
    
    def get_pattern_details(self, pattern_key: str) -> Optional[Dict]:
        """Get full details for a specific pattern."""
        return self.patterns.get(pattern_key)
    
    def list_patterns_for_species(self, species: str) -> List[str]:
        """List all known patterns for a species."""
        return [
            key for key, pattern in self.patterns.items()
            if pattern['species'] == species
        ]


# ============================================================================
# Real-Time Pattern Recognition
# ============================================================================

class RealTimePatternRecognizer:
    """
    Real-time pattern recognition for live FCI data streams.
    
    Maintains sliding window of recent spikes and continuously
    classifies against known patterns.
    """
    
    def __init__(self, window_duration_minutes: float = 60):
        """
        Args:
            window_duration_minutes: How much history to consider
        """
        self.classifier = SignalPatternClassifier()
        self.window_duration = window_duration_minutes
        self.spike_buffer: List[Dict] = []
        
    def add_spike(self, timestamp: float, amplitude: float):
        """
        Add new spike to buffer and update classification.
        
        Args:
            timestamp: Spike time (seconds since start)
            amplitude: Spike amplitude (mV)
        """
        self.spike_buffer.append({
            'timestamp': timestamp,
            'amplitude': amplitude
        })
        
        # Remove old spikes outside window
        cutoff_time = timestamp - (self.window_duration * 60)
        self.spike_buffer = [
            s for s in self.spike_buffer 
            if s['timestamp'] >= cutoff_time
        ]
    
    def get_current_classification(self) -> Dict:
        """
        Classify current spike train in buffer.
        
        Returns:
            Classification results with pattern matches
        """
        if len(self.spike_buffer) < 2:
            return {
                'pattern_matches': [],
                'species_probabilities': {},
                'confidence': 'insufficient_data'
            }
        
        # Calculate spike train characteristics
        timestamps = [s['timestamp'] for s in self.spike_buffer]
        amplitudes = [s['amplitude'] for s in self.spike_buffer]
        
        intervals = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
        avg_interval_minutes = (np.mean(intervals) / 60) if intervals else 0
        
        duration_minutes = (timestamps[-1] - timestamps[0]) / 60
        
        spike_train_data = {
            'spike_count': len(self.spike_buffer),
            'duration_minutes': duration_minutes,
            'avg_amplitude_mv': np.mean(amplitudes),
            'avg_interval_minutes': avg_interval_minutes
        }
        
        # Classify
        pattern_matches = self.classifier.classify_spike_train(
            spike_train_data['spike_count'],
            spike_train_data['duration_minutes'],
            spike_train_data['avg_amplitude_mv'],
            spike_train_data['avg_interval_minutes']
        )
        
        species_probs = self.classifier.identify_species(spike_train_data)
        
        return {
            'pattern_matches': pattern_matches,
            'species_probabilities': species_probs,
            'spike_train_data': spike_train_data,
            'confidence': 'high' if pattern_matches and pattern_matches[0][1] > 0.7 else 'medium' if pattern_matches else 'low'
        }


# ============================================================================
# Pattern Generation for Testing
# ============================================================================

def generate_synthetic_pattern(
    pattern_key: str,
    duration_minutes: float,
    noise_level: float = 0.1
) -> List[Dict]:
    """
    Generate synthetic spike train matching a known pattern.
    
    Useful for testing, simulation, and educational demos.
    
    Args:
        pattern_key: Key from SPIKE_TRAIN_PATTERNS
        duration_minutes: How long to generate
        noise_level: 0-1, amount of randomness
        
    Returns:
        List of {timestamp, amplitude} dicts
    """
    if pattern_key not in SPIKE_TRAIN_PATTERNS:
        return []
    
    pattern = SPIKE_TRAIN_PATTERNS[pattern_key]
    spikes = []
    
    # Extract pattern parameters
    spike_count = int(np.mean(pattern['spike_count_range']))
    avg_amplitude = np.mean(pattern['amplitude_range'])
    avg_interval = duration_minutes / spike_count
    
    current_time = 0
    
    for i in range(spike_count):
        # Add noise to interval
        interval = avg_interval * (1 + (np.random.random() - 0.5) * noise_level)
        current_time += interval * 60  # Convert to seconds
        
        # Add noise to amplitude
        amplitude = avg_amplitude * (1 + (np.random.random() - 0.5) * noise_level * 0.5)
        
        # Special patterns
        if "wave" in pattern_key:
            # Wave packet: amplitude increases then decreases
            progress = i / spike_count
            envelope = np.sin(progress * np.pi)  # 0 to 1 to 0
            amplitude *= (0.5 + envelope * 0.5)
        
        spikes.append({
            'timestamp': current_time,
            'amplitude': amplitude
        })
    
    return spikes


# ============================================================================
# Mycorrhizae Protocol Integration
# ============================================================================

def classify_fci_message(fci_message: Dict) -> Dict:
    """
    Classify FCI message from Mycorrhizae Protocol stream.
    
    Args:
        fci_message: Message from FCI device with telemetry
        
    Returns:
        Classification results to enrich message
    """
    # Extract spike data from message
    if 'spike_event' in fci_message:
        recognizer = RealTimePatternRecognizer()
        
        # Add recent spikes
        for spike in fci_message.get('recent_spikes', []):
            recognizer.add_spike(spike['timestamp'], spike['amplitude'])
        
        # Classify
        classification = recognizer.get_current_classification()
        
        # Add to message
        fci_message['classification'] = classification
        fci_message['enriched'] = True
        fci_message['classifier_version'] = '1.0_literature_based'
    
    return fci_message


if __name__ == "__main__":
    # Demo classification
    classifier = SignalPatternClassifier()
    
    # Test with S. commune characteristics
    result = classifier.classify_spike_train(
        spike_count=15,
        duration_minutes=60,
        avg_amplitude_mv=0.04,
        avg_interval_minutes=4
    )
    
    print("Pattern matches:")
    for pattern_name, confidence in result:
        pattern = classifier.get_pattern_details(pattern_name)
        print(f"  {pattern_name}: {confidence:.2%}")
        print(f"    Species: {pattern['species']}")
        print(f"    Description: {pattern['description']}")
