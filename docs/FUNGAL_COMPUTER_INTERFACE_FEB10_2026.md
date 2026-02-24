# Fungal Computer Interface (FCI)

**Date:** February 10, 2026  
**Author:** Mycosoft Labs  
**Status:** Hardware Integration in Development

---

## Executive Summary

The **Fungal Computer Interface (FCI)** is a pioneering technology that enables unprecedented direct communication, computation, and interaction with complex fungal mycelium networks. By tapping into the natural intelligence of fungi—organisms renowned for their intricate underground networks and sophisticated signal processing—FCIs represent a crucial step toward integrating biological systems with digital infrastructures.

This new class of bio-hybrid technology does more than just read fungal signals: it uses specialized hardware and software to **converse** with the mycelium, transforming subtle electrical patterns and chemical gradients into actionable digital data. The FCI fundamentally redefines what it means to interface with life-based systems, offering a paradigm shift from traditional computing models reliant on silicon and semiconductors to one that acknowledges, leverages, and respects the complexity inherent in nature's oldest networks.

---

## What is a Fungal Computer Interface?

A **Fungal Computer Interface (FCI)** is a technological construct that creates a **two-way communication channel** between fungal mycelium and digital computing systems. Using specialized sensors, signal processing hardware, and custom software, FCIs convert fungal bioelectric and biochemical signals into digital data streams.

### Core Capabilities

| Capability | Description |
|------------|-------------|
| **Signal Reading** | Capture bioelectric activity from mycelium (microvolts to millivolts) |
| **Signal Writing** | Send electrical stimuli back to mycelium for experimentation |
| **Pattern Recognition** | Identify and classify fungal signal patterns |
| **Environmental Sensing** | Detect fungi's response to external stimuli |
| **Biological Computation** | Use mycelium as a living computational substrate |

---

## Architecture

### The Three Components

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     FUNGAL COMPUTER INTERFACE                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐ │
│   │                 │     │                  │     │                 │ │
│   │  FUNGAL PROBE   │────▶│ SIGNAL PROCESSOR │────▶│ CLOUD/ANALYSIS  │ │
│   │                 │◀────│                  │◀────│                 │ │
│   │ • Electrodes    │     │ • Amplification  │     │ • NatureOS      │ │
│   │ • Sensors       │     │ • Filtering      │     │ • MINDEX        │ │
│   │ • Substrate     │     │ • ADC            │     │ • HPL Runtime   │ │
│   │                 │     │ • MCU            │     │ • ML Models     │ │
│   └─────────────────┘     └──────────────────┘     └─────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1. Fungal Probe

The heart of the FCI—an assembly of bio-compatible electrodes and sensors placed in or alongside fungal substrate.

**Electrode Materials:**
| Material | Properties | Best For |
|----------|------------|----------|
| Stainless Steel | Durable, corrosion-resistant | General use |
| Carbon Fiber/Graphite | Good conductivity, stable potential | Sensitive readings |
| PEDOT:PSS | Flexible, conformal contact | Advanced applications |
| Silver/Silver Chloride | Low noise, stable reference | High-precision |

**Sensor Types:**
- Bioelectric electrodes (ECG/EMG/EEG style)
- Humidity sensors
- pH sensors
- Temperature probes
- Volatile organic compound (VOC) detectors

**Placement Guidelines:**
- Multiple electrodes spaced 2-5 cm apart
- Consistent depth (typically 1-3 cm into substrate)
- Minimal disturbance to mycelial network
- Reference electrode in nutrient-free zone

### 2. Signal Processing Unit

Converts raw bioelectric signals into clean digital data.

**Signal Conditioning Chain:**

```
Electrode → Buffer Amp → Instrumentation Amp → Bandpass Filter → ADC → MCU
           (high Z)      (INA128/AD620)       (0.1-50 Hz)      (12+ bit)
```

**Key Specifications:**
| Parameter | Requirement |
|-----------|-------------|
| Input impedance | >10 MΩ |
| CMRR | >80 dB |
| Noise floor | <1 μV RMS |
| Sample rate | 100-1000 Hz |
| ADC resolution | 12-16 bit |
| Bandwidth | 0.1-50 Hz typical |

**Microcontroller Options:**
- ESP32 (WiFi, Bluetooth, low power)
- Raspberry Pi (full Linux, ML capable)
- Arduino (simple, well-documented)
- STM32 (high performance, low power)

### 3. Cloud Integration

Real-time processing and analysis via Mycosoft infrastructure.

**Data Flow:**
1. MCU captures and filters signal
2. Transmit via WiFi/LoRa/Cellular to Mycorrhizae Protocol
3. Store in MINDEX database
4. Process through HPL programs
5. Display in NatureOS dashboard
6. Trigger alerts/actions as needed

---

## Hardware Devices

### Mushroom 1

**Purpose:** Ground-penetrating sensor for in-situ mycelium monitoring

**Specifications:**
- ECG/EMG/EEG-style probe for bioelectric signals
- Environmental sensors (temperature, humidity, soil moisture)
- ESP32-based MCU
- Solar/battery powered
- LoRa connectivity for remote deployment
- Weatherproof enclosure

**Channels:**
- `device.mushroom1-{serial}.bioelectric`
- `device.mushroom1-{serial}.environment`
- `device.mushroom1-{serial}.commands`

### SporeBase

**Purpose:** Controlled cultivation monitoring and automation

**Specifications:**
- Multi-electrode array for culture monitoring
- Climate control integration (temperature, humidity, CO2)
- Camera for visual monitoring
- Automated misting/heating/lighting control
- USB/Ethernet connectivity

### MycoBrain

**Purpose:** Modular field-deployable sensor platform

**Specifications:**
- ESP32-S3 dual-core MCU
- BME688/690 environmental sensors
- Bioelectric input channels
- Serial communication (MDP protocol)
- Battery powered with solar option
- Compact weatherproof design

**Current Firmware:** See `mycobrain/firmware/`

### TruffleBot

**Purpose:** Mobile soil exploration robot

**Specifications:**
- Motorized platform for soil traversal
- Retractable probe for mycelium sampling
- GPS/GNSS for location tracking
- Autonomous navigation capability
- Wireless data relay

---

## Software Integration

### FCI Interface Module

**Location:** `mycorrhizae/fci/interface.py`

```python
from mycorrhizae.fci import FCIInterface, FCISignalType

# Initialize interface for a device
fci = FCIInterface(device_serial="MCB-2026-0001")

# Record readings from sensors
fci.record_reading(
    sensor_id="bioelectric_1",
    raw_value=-15.3,  # microvolts
    unit="uV",
    quality=0.95
)

# Get aggregate statistics
stats = fci.get_aggregate_stats()

# Convert to message format
payload = fci.to_mycorrhizae_payload()
```

### Signal Types

| Signal Type | Description | Typical Range |
|-------------|-------------|---------------|
| `bioelectric` | Electrical activity from mycelium | -100 to +100 μV |
| `impedance` | Electrical resistance of substrate | 100-10000 Ω |
| `conductivity` | Ion concentration indicator | 100-5000 μS/cm |
| `temperature` | Substrate temperature | 5-40 °C |
| `humidity` | Moisture level | 0-100% |
| `ph` | Acidity/alkalinity | 4-9 |
| `voc` | Volatile organic compounds | 0-500 ppm |
| `co2` | Carbon dioxide level | 400-5000 ppm |

### HPL Integration

FCI data can be processed through HPL programs:

```hpl
# Read from FCI device
hypha bioelectric = sense("bioelectric")
hypha impedance = sense("impedance")
hypha temperature = sense("temperature")

# Build signal history
grow bioelectric_history bioelectric

# Analyze patterns
hypha activity_level = avg("bioelectric_history")
hypha signal_variance = stddev("bioelectric_history")

# Detect anomalies
branch signal_variance > 20 {
  emit("alerts", {
    type: "high_activity",
    variance: signal_variance,
    mean: activity_level
  })
}

# Output processed data
fruit("fci_reading", {
  bioelectric: bioelectric,
  impedance: impedance,
  temperature: temperature,
  activity_level: activity_level,
  signal_health: branch(signal_variance < 50, "stable", "volatile")
})
```

---

## Building Your Own FCI

### Bill of Materials

| Component | Example Part | Est. Cost |
|-----------|--------------|-----------|
| Microcontroller | ESP32-S3 DevKit | $15 |
| Instrumentation Amp | INA128 | $8 |
| ADC (if external) | ADS1115 | $5 |
| Electrodes | Stainless steel pins | $2 |
| Enclosure | IP65 weatherproof box | $10 |
| Power | 18650 battery + charger | $10 |
| Sensors | BME688 | $20 |
| Misc (PCB, wires, etc.) | - | $20 |
| **Total** | | **~$90** |

### Circuit Schematic (Simplified)

```
                    ┌──────────────┐
    Electrode 1 ───▶│ INA128       │
                    │ Instr. Amp   │──▶ ADC ──▶ ESP32 GPIO
    Electrode 2 ───▶│              │
                    └──────────────┘
    
    Reference ───────────────────────▶ Ground
    
    BME688 ─────── I2C ───────────────▶ ESP32 I2C
```

### Firmware Example (Arduino/ESP32)

```cpp
#include <Wire.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <Adafruit_ADS1X15.h>

Adafruit_ADS1115 ads;

const char* MYCORRHIZAE_URL = "http://192.168.0.188:8002";
const char* API_KEY = "mcr_device_key";
const char* DEVICE_ID = "FCI-001";

void setup() {
    Serial.begin(115200);
    ads.begin();
    WiFi.begin("SSID", "password");
    while (WiFi.status() != WL_CONNECTED) delay(100);
}

void loop() {
    // Read bioelectric signal (differential)
    int16_t raw = ads.readADC_Differential_0_1();
    float microvolts = ads.computeVolts(raw) * 1000000;
    
    // Send to Mycorrhizae
    publishReading("bioelectric", microvolts, "uV");
    
    delay(100); // 10 Hz sample rate
}

void publishReading(const char* sensor, float value, const char* unit) {
    HTTPClient http;
    String channel = String("device.") + DEVICE_ID + ".telemetry";
    String url = String(MYCORRHIZAE_URL) + "/api/channels/" + channel + "/publish";
    
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-API-Key", API_KEY);
    
    String body = "{\"payload\":{\"" + String(sensor) + "\":" + 
                  String(value) + ",\"unit\":\"" + unit + "\"}}";
    
    http.POST(body);
    http.end();
}
```

### Signal Processing (Python)

```python
import numpy as np
from scipy.signal import butter, filtfilt, welch

def bandpass_filter(data, lowcut=0.1, highcut=50, fs=100, order=4):
    """Apply bandpass filter to remove noise."""
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return filtfilt(b, a, data)

def extract_features(signal, fs=100):
    """Extract features from bioelectric signal."""
    # Time domain
    mean_val = np.mean(signal)
    std_val = np.std(signal)
    rms = np.sqrt(np.mean(signal**2))
    
    # Frequency domain
    freqs, psd = welch(signal, fs=fs)
    dominant_freq = freqs[np.argmax(psd)]
    total_power = np.sum(psd)
    
    return {
        "mean": mean_val,
        "std": std_val,
        "rms": rms,
        "dominant_frequency": dominant_freq,
        "total_power": total_power
    }

def detect_spike(signal, threshold=3.0):
    """Detect action potential-like spikes."""
    z_scores = (signal - np.mean(signal)) / np.std(signal)
    spikes = np.where(np.abs(z_scores) > threshold)[0]
    return spikes
```

---

## Applications

### 1. Environmental Monitoring

- Detect pollution through mycelial stress responses
- Monitor soil health in real-time
- Track contaminant migration through ecosystems
- Early warning for ecological disturbances

### 2. Biological Computation

- Use mycelium as living logic gates
- Distributed problem-solving (shortest path, optimization)
- Self-healing, adaptive computational systems
- Energy-efficient bio-hybrid computing

### 3. Precision Agriculture

- Real-time soil nutrient monitoring
- Early disease/pest detection
- Optimized irrigation scheduling
- Symbiotic relationship management

### 4. Seismic Prediction (M-Wave)

- Detect earthquake precursors through impedance changes
- Distributed sensor networks for triangulation
- Machine learning for pattern recognition
- Early warning system integration

### 5. Astrobiology

- Study fungal analogs on other planets
- Simulate extraterrestrial conditions
- Develop detection methods for non-terrestrial life
- Inform Mars/Moon habitat design

---

## Current Implementation Status

### Implemented

| Component | Location | Status |
|-----------|----------|--------|
| FCI Interface module | `mycorrhizae/fci/interface.py` | Basic |
| Signal types enum | `mycorrhizae/fci/interface.py` | Complete |
| Channel conventions | `mycorrhizae/fci/interface.py` | Complete |
| MycoBrain firmware | `mycobrain/firmware/` | Partial |
| Mycorrhizae routing | VM 188:8002 | Active |

### Planned

| Component | Priority | Target |
|-----------|----------|--------|
| Full bioelectric driver | HIGH | Q1 2026 |
| Two-way communication | HIGH | Q2 2026 |
| ML pattern recognition | MEDIUM | Q2 2026 |
| Mushroom 1 production | MEDIUM | Q3 2026 |
| SporeBase integration | LOW | Q4 2026 |

---

## Related Documentation

- [Global Fungi Symbiosis Theory](./GLOBAL_FUNGI_SYMBIOSIS_THEORY_FEB10_2026.md)
- [HPL Language Guide](./HPL_LANGUAGE_GUIDE_FEB10_2026.md)
- [Mycorrhizae Protocol Overview](./MYCORRHIZAE_PROTOCOL_OVERVIEW_FEB10_2026.md)
- [FCI White Paper on Medium](https://medium.com/@mycosoft.inc/fungal-computer-interface-fci-c0c444611cc1)
