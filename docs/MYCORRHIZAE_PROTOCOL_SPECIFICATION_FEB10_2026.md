# Mycorrhizae Protocol v1.0 Specification

**Date**: February 10, 2026  
**Version**: 1.0.0  
**Authors**: Mycosoft Labs  
**Status**: Draft

---

## Executive Summary

The Mycorrhizae Protocol is a novel biological computing communication protocol designed for bidirectional information exchange between computational systems and fungal mycelial networks. Unlike conventional IoT protocols that merely route raw sensor data, Mycorrhizae interprets bioelectric signals through the lens of **Global Fungi Symbiosis Theory (GFST)**, translating fungal responses into semantically meaningful information about environmental states, ecological dynamics, and potentially even precursor signals for geological events.

This protocol is the first of its kind: **a bridge between biological intelligence and digital computation**.

---

## 1. Theoretical Foundation

### 1.1 Biophysics of Mycelial Signaling

Fungal networks exhibit electrical signaling analogous to, but distinct from, neuronal systems:

| Property | Neurons | Mycelium | Implications |
|----------|---------|----------|--------------|
| Resting potential | -70 mV | -50 to -100 mV | Comparable baseline |
| Action potential amplitude | 100 mV | 0.5-5 mV | Lower amplitude, higher sensitivity needed |
| Propagation velocity | 1-100 m/s | 0.5-50 mm/min | Much slower, integrative |
| Ion channels | Na⁺, K⁺, Ca²⁺ | K⁺, Ca²⁺, H⁺ | Different ionic basis |
| Membrane time constant | 1-100 ms | 1-100 s | Longer integration windows |

**Key equations:**

1. **Membrane potential (Goldman-Hodgkin-Katz):**
   ```
   V_m = (RT/F) × ln((P_K[K⁺]_o + P_Na[Na⁺]_o + P_Ca[Ca²⁺]_o) / (P_K[K⁺]_i + P_Na[Na⁺]_i + P_Ca[Ca²⁺]_i))
   ```

2. **Action potential propagation (cable theory):**
   ```
   λ = √(r_m / r_i)   [space constant]
   τ = r_m × c_m      [time constant]
   v = λ / τ          [propagation velocity]
   ```

3. **Signal attenuation:**
   ```
   V(x) = V_0 × e^(-x/λ)
   ```

### 1.2 Chemical Signaling Components

Mycelium communicate through volatile organic compounds (VOCs) and non-volatile metabolites:

| Compound Class | Function | Detection Method |
|----------------|----------|------------------|
| Terpenoids (e.g., β-caryophyllene) | Defense, alarm | BME688 VOC sensor |
| Alcohols (1-octen-3-ol) | Stress, damage | Gas chromatography |
| Oxylipins | Reproductive signaling | Mass spectrometry |
| ATP/ADP | Energy state | Bioluminescence assay |
| Trehalose | Stress protection | Enzymatic assay |

### 1.3 GFST Signal Patterns

Based on published research and our experimental observations:

| Pattern Name | Frequency Range | Amplitude Range | Duration | Environmental Trigger |
|--------------|-----------------|-----------------|----------|----------------------|
| Baseline | 0-0.5 Hz | 0-0.3 µV | Continuous | None (resting) |
| Growth | 0.1-5 Hz | 0.5-2 µV | >1s | Nutrients, favorable conditions |
| Stress | 5-20 Hz | 1-10 µV | Variable | Temperature, toxins, dessication |
| Nutrient-seeking | 0.5-3 Hz | 0.3-1.5 µV | >5s | Chemical gradients |
| Communication | 1-10 Hz | 0.5-5 µV | Variable | Inter-network events |
| Seismic precursor | 0.01-0.1 Hz | 0.1-1 µV | >1hr | Tectonic stress changes |
| Action potential | Spike | 2-100 µV | 5-100 ms | Rapid environmental change |

---

## 2. Protocol Architecture

### 2.1 Layer Model

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 5: Application          │ HPL Programs, Pattern Matching  │
├─────────────────────────────────────────────────────────────────┤
│ Layer 4: Semantic Translation │ GFST Pattern → Meaning          │
├─────────────────────────────────────────────────────────────────┤
│ Layer 3: Signal Processing    │ Filtering, FFT, Feature Extract │
├─────────────────────────────────────────────────────────────────┤
│ Layer 2: Transport            │ WebSocket, MQTT, CoAP, Serial   │
├─────────────────────────────────────────────────────────────────┤
│ Layer 1: Physical             │ FCI Probes → ADS1115 → ESP32    │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

```
Mycelium → Electrodes → Instrumentation Amp → ADC → ESP32 
    → DSP (filtering, FFT) → Pattern Detection → Semantic Translation 
    → Mycorrhizae Envelope → Transport → Cloud/Edge Processing
    → HPL Program → Actions/Storage/Visualization
```

### 2.3 Bidirectional Communication

**Read path (Sensing):**
```
Mycelium bioelectric → FCI probe → ADC → Signal processing → Pattern → Meaning
```

**Write path (Stimulation):**
```
HPL command → Validation → Waveform generation → DAC → Electrode → Mycelium
```

---

## 3. Message Format

### 3.1 Envelope Structure

All Mycorrhizae messages use a standardized envelope format:

```json
{
  "version": "1.0.0",
  "id": "uuid-v4",
  "timestamp": "2026-02-10T12:34:56.789Z",
  "expires": "2026-02-10T13:34:56.789Z",
  "channel": "device.{device_id}.{message_type}",
  
  "source": {
    "type": "fci|environment|gateway|simulator",
    "device_id": "uuid",
    "device_serial": "MAC or serial",
    "firmware_version": "1.0.0",
    "probe_type": "type_a|type_b|type_c|type_d",
    "location": {
      "latitude": 47.6062,
      "longitude": -122.3321,
      "altitude_m": 56,
      "accuracy_m": 5
    }
  },
  
  "signature": {
    "algorithm": "ed25519",
    "public_key": "base64...",
    "signature": "base64..."
  },
  
  "payload": { /* message-type specific */ }
}
```

### 3.2 Message Types

#### 3.2.1 FCI Telemetry (`fci_telemetry`)

```json
{
  "payload": {
    "bioelectric": {
      "channels": [
        {
          "id": "bio_1",
          "amplitude_uv": 1.23,
          "rms_uv": 0.87,
          "mean_uv": 0.12,
          "std_uv": 0.34,
          "dominant_freq_hz": 2.5,
          "spectral_centroid_hz": 3.1,
          "total_power": 0.56,
          "band_powers": {
            "ultra_low": 0.01,  // 0.01-0.1 Hz
            "low": 0.12,         // 0.1-1 Hz
            "mid": 0.35,         // 1-10 Hz
            "high": 0.08         // 10-50 Hz
          },
          "snr_db": 23.5,
          "quality_score": 0.92
        }
      ],
      "cross_correlation": {
        "channels": ["bio_1", "bio_2"],
        "correlation": 0.85,
        "lag_ms": 12.5,
        "propagation_velocity_mm_per_min": 24.0
      }
    },
    
    "pattern": {
      "detected": "growth",
      "confidence": 0.87,
      "alternatives": [
        {"pattern": "baseline", "confidence": 0.12}
      ],
      "spike_count": 3,
      "spike_rate_hz": 0.15
    },
    
    "environment": {
      "temperature_c": 22.5,
      "humidity_pct": 85.0,
      "pressure_hpa": 1013.25,
      "voc_index": 125,
      "co2_ppm": 450
    },
    
    "stimulus": {
      "active": false,
      "waveform": null,
      "amplitude_uv": null,
      "frequency_hz": null
    },
    
    "device_status": {
      "uptime_ms": 3600000,
      "wifi_rssi_dbm": -45,
      "battery_pct": 85,
      "impedance_ohms": 50000,
      "last_calibration": "2026-02-10T08:00:00Z"
    }
  }
}
```

#### 3.2.2 Pattern Event (`pattern_event`)

Emitted when a significant pattern is detected:

```json
{
  "payload": {
    "event_type": "pattern_detected",
    "pattern": {
      "name": "StressResponse",
      "category": "stress",
      "confidence": 0.92,
      "start_time": "2026-02-10T12:30:00Z",
      "duration_ms": 15000,
      "features": {
        "amplitude_uv": 5.2,
        "frequency_hz": 12.5,
        "waveform": "aperiodic"
      }
    },
    "context": {
      "preceding_pattern": "growth",
      "environmental_delta": {
        "temperature_c": -2.5,
        "humidity_pct": -5.0
      }
    },
    "interpretation": {
      "semantic": "Environmental stress detected - possible temperature drop response",
      "severity": "moderate",
      "recommended_action": "monitor for recovery within 30 minutes"
    }
  }
}
```

#### 3.2.3 Stimulus Command (`stimulus_command`)

Commands for bidirectional communication:

```json
{
  "payload": {
    "command": "start_stimulus",
    "parameters": {
      "waveform": "pulse|sine|ramp|dc|custom",
      "amplitude_uv": 50.0,
      "frequency_hz": 1.0,
      "duration_ms": 5000,
      "custom_samples": [/* optional for custom waveform */]
    },
    "safety": {
      "max_amplitude_uv": 100.0,
      "max_duration_ms": 60000,
      "require_confirmation": true
    }
  }
}
```

---

## 4. Semantic Translation Layer

### 4.1 Pattern → Meaning Mapping

The semantic translation layer converts detected patterns into actionable insights:

```python
SEMANTIC_MAPPINGS = {
    "GrowthSignal": {
        "meaning": "Active hyphal extension and resource acquisition",
        "ecological_state": "healthy_growth",
        "action_suggestions": [
            "Maintain current environmental conditions",
            "Monitor for nutrient depletion"
        ],
        "confidence_threshold": 0.7
    },
    "StressResponse": {
        "meaning": "Environmental stress detected",
        "ecological_state": "stress",
        "action_suggestions": [
            "Check recent environmental changes",
            "Verify temperature, humidity within optimal range",
            "Monitor for pathogen presence"
        ],
        "urgency": "moderate"
    },
    "SeismicPrecursor": {
        "meaning": "Potential geological activity precursor (M-Wave)",
        "ecological_state": "warning",
        "action_suggestions": [
            "Correlate with geological monitoring data",
            "Log for long-term pattern analysis",
            "Alert if confidence exceeds 0.8"
        ],
        "urgency": "high",
        "confidence_threshold": 0.6
    }
}
```

### 4.2 Confidence Calibration

Pattern confidence is calibrated using:

1. **Signal quality score** (0-1)
2. **Pattern feature matching** (weighted average of constraint matches)
3. **Historical context** (how well does this fit recent patterns?)
4. **Environmental consistency** (do environmental conditions support this interpretation?)

```
final_confidence = (
    0.4 × feature_match_confidence +
    0.2 × signal_quality +
    0.2 × historical_consistency +
    0.2 × environmental_support
)
```

---

## 5. Transport Layer

### 5.1 Supported Transports

| Transport | Use Case | QoS | Latency |
|-----------|----------|-----|---------|
| WebSocket | Real-time streaming | Ordered delivery | <100ms |
| MQTT | IoT integration | QoS 0/1/2 | Variable |
| CoAP | Low-power devices | Confirmable | Variable |
| HTTP/REST | Request-response | N/A | Variable |
| Serial | Direct connection | N/A | <10ms |

### 5.2 Channel Naming Convention

```
{message_class}.{source_id}.{message_type}

Examples:
device.550e8400-e29b-41d4-a716-446655440000.telemetry
device.550e8400-e29b-41d4-a716-446655440000.pattern_event
gateway.main.aggregated_telemetry
simulator.petri_001.telemetry
```

### 5.3 Message Security

All messages are signed using Ed25519:

```
1. Serialize payload to canonical JSON
2. Compute SHA-256 hash of payload
3. Sign hash with device's Ed25519 private key
4. Include public key and signature in envelope
```

Verification on receiver:
```
1. Extract payload and signature
2. Verify signature using included public key
3. Verify public key against device registry
4. Accept or reject message
```

---

## 6. Physical Layer Specifications

### 6.1 Electrode Materials

Based on Mycosoft FCI probe experiments:

| Material | Pros | Cons | Best For |
|----------|------|------|----------|
| Copper | Low cost, good conductivity | Oxidation, potential toxicity | Short-term experiments |
| Silver/AgCl | Low noise, stable | Cost, light sensitivity | Reference electrode |
| Platinum | Inert, biocompatible | High cost | Long-term monitoring |
| Platinum-Iridium | Most stable, durable | Very high cost | Precision research |
| Carbon fiber | Minimal interference, flexible | Lower conductivity | Dense networks |

### 6.2 Agar Interface

For mycelium interaction incentive:
- **Concentration**: 1.5-3% agar
- **Nutrients**: Minimal (to encourage growth toward electrodes)
- **Thickness**: 2-5mm between electrode pairs

### 6.3 Signal Conditioning

```
Mycelium → Differential electrodes → Instrumentation amplifier (INA128, gain=1000)
    → Bandpass filter (0.1-50 Hz, 4th order Butterworth)
    → Notch filter (50/60 Hz)
    → ADC (ADS1115, 16-bit, 128 SPS)
```

---

## 7. Implementation Reference

### 7.1 Minimum Viable Implementation

A conformant Mycorrhizae Protocol implementation MUST:

1. Generate valid envelope structure with required fields
2. Implement at least `fci_telemetry` message type
3. Include device identification and timestamp
4. Support at least one transport (WebSocket recommended)

SHOULD:
5. Implement Ed25519 message signing
6. Support pattern detection with at least `baseline`, `growth`, `stress`
7. Include environmental sensor data
8. Implement calibration routines

### 7.2 Interoperability

Implementations MUST:
- Use UTC timestamps in ISO 8601 format
- Use UUIDs for message and device IDs
- Serialize JSON without trailing commas
- Support both IPv4 and IPv6

---

## 8. MINDEX Integration

All Mycorrhizae data flows to MINDEX for:

1. **Signal storage**: Raw and processed signals in time-series format
2. **Pattern database**: Detected patterns with features and confidence
3. **Semantic events**: High-level interpretations and alerts
4. **ML training data**: Labeled signals for improving pattern detection

MINDEX schema requirements documented in `MINDEX_SIGNAL_SCHEMA_*.md`.

---

## 9. References

1. Adamatzky, A. (2018). "On spiking behaviour of oyster fungi Pleurotus djamor." *Scientific Reports*.
2. Olsson, S., & Hansson, B. S. (1995). "Action potential-like activity found in fungal mycelia is sensitive to stimulation." *Naturwissenschaften*.
3. Simard, S. W. (2018). "Mycorrhizal Networks and Seedling Establishment in Douglas-fir Forests." *Chapter in Mycorrhizal Mediation of Soil*.
4. Bebber, D. P., et al. (2007). "Biological solutions to transport network design." *Proceedings of the Royal Society B*.
5. Fukasawa, Y. (2021). "Fungal electricity: a promising pathway for fungal biotech." *Trends in Biotechnology*.

---

## Appendix A: Constants

```python
# Protocol version
PROTOCOL_VERSION = "1.0.0"

# Frequency bands (Hz)
FREQ_ULTRA_LOW = (0.01, 0.1)   # Seismic, slow metabolic
FREQ_LOW = (0.1, 1.0)          # Growth, slow activity
FREQ_MID = (1.0, 10.0)         # Active processes
FREQ_HIGH = (10.0, 50.0)       # Fast activity, stress

# Amplitude ranges (µV)
AMP_BASELINE = (0.0, 0.3)
AMP_GROWTH = (0.5, 2.0)
AMP_STRESS = (1.0, 10.0)
AMP_SPIKE = (2.0, 100.0)

# Timing
MIN_SAMPLE_RATE_HZ = 10
RECOMMENDED_SAMPLE_RATE_HZ = 128
MAX_MESSAGE_AGE_S = 3600
DEFAULT_TTL_S = 3600
```

---

**Document Status**: Living document - updates as protocol evolves.

**Feedback**: protocol@mycosoft.com
