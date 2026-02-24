# HPL Language Guide - Hypha Programming Language

**Date:** February 10, 2026  
**Version:** 1.0.0  
**Location:** `mycorrhizae/hpl/`

---

## Overview

**HPL (Hypha Programming Language)** is a novel, interdisciplinary programming language designed to facilitate computational interaction with fungi, specifically mycelial networks. HPL bridges the gap between biological electrical signaling in fungi and digital computing systems, integrating principles from physics, chemistry, biology, and computer science.

Inspired by the structure and behavior of fungal mycelium networks, HPL uses biological metaphors to create intuitive programs for sensor data processing, alerting, and analysis.

### Vision vs Current Implementation

> **Note:** HPL is being developed in phases. This document covers both the **current implementation** (what works today) and the **full vision** (what's planned).

| Feature | Current | Planned | Status |
|---------|---------|---------|--------|
| Core keywords (8) | Yes | Yes | **COMPLETE** |
| Statistical functions | Yes | Yes | **COMPLETE** |
| Alert functions | Yes | Yes | **COMPLETE** |
| Signal Pattern Language (SPL) | No | Yes | PLANNED |
| Device Interface Modules | No | Yes | PLANNED |
| MINDEX Integration | No | Yes | PLANNED |
| Signal data type | No | Yes | PLANNED |
| Signal processing operators | No | Yes | PLANNED |
| Two-way fungal communication | No | Yes | PLANNED |
| Compiler + Virtual Machine | No | Yes | PLANNED |

### Core Objectives

HPL is designed to:

1. **Normalize and Categorize Fungal Data** - Use the MINDEX database and APIs to store and organize data from devices and sensors
2. **Interface with Devices** - Seamlessly interact with Mushroom 1, SporeBase, TruffleBot, and MycoBrain
3. **Implement the Mycorrhizae Protocol** - Standardized communication for data exchange between fungi and digital systems
4. **Validate the Global Fungi Symbiosis Theory** - Analyze electrical patterns to understand fungi's responses to environmental stimuli
5. **Develop a Common Language of Electrical Signals** - Create consistent methods for reading from and writing to mycelial networks

### Design Philosophy

HPL treats sensor data processing like a growing mycelium network:
- **Hyphae** (fungal threads) represent individual data values and variables
- **Branching** represents conditional logic, like mycelium branching in response to nutrients
- **Growing** represents data accumulation, like network expansion
- **Sensing** represents environmental awareness, like fungal chemotaxis
- **Fruiting** represents final output, like mushrooms producing spores
- **Decay** represents cleanup, like fungal decomposition

---

## Quick Start

```hpl
# Read temperature from sensor
hypha temp = sense("temperature")

# Check threshold and alert
branch temp > 30 {
  emit("alerts", {type: "high_temp", value: temp})
}

# Accumulate history for analysis
grow temp_history temp

# Produce final output with average
fruit("analysis", {avg_temp: avg("temp_history"), trend: trend("temp_history")})
```

---

## Keywords

HPL uses biological metaphors for all keywords:

| Keyword | Traditional | Description |
|---------|-------------|-------------|
| `hypha` | `var`/`let` | Variable declaration |
| `sense` | `read` | Read sensor data |
| `emit` | `output` | Send signal to channel |
| `branch` | `if` | Conditional execution |
| `grow` | `accumulate` | Build history over time |
| `fruit` | `return` | Produce final output |
| `decay` | `delete` | Clean up resources |
| `spawn` | `create` | Start new process (future) |
| `mycelium` | `array` | Collection type (future) |
| `substrate` | `context` | Environment data (future) |
| `enzyme` | `function` | Function definition (future) |

---

## Core Statements

### Variable Declaration: `hypha`

Create a named variable (like a hypha thread in a mycelium network).

**Syntax:**
```hpl
hypha name = expression
```

**Examples:**
```hpl
# Simple assignment
hypha temperature = 22.5

# From sensor reading
hypha temp = sense("temperature")

# Expression
hypha delta = sense("temperature") - 20.0

# Object
hypha reading = {
  value: sense("temperature"),
  quality: sense("temperature", "quality"),
  timestamp: now()
}
```

---

### Sensor Reading: `sense`

Read data from a sensor (like fungal hyphae sensing their environment).

**Syntax:**
```hpl
sense("sensor_id")
sense("sensor_id", "field")
```

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `"value"` | float | Current sensor value (default) |
| `"quality"` | float | Signal quality 0-1 |
| `"timestamp"` | float | Unix timestamp of reading |
| `*` | any | Custom metadata field |

**Examples:**
```hpl
# Read temperature value
hypha temp = sense("temperature")

# Read with quality check
hypha quality = sense("impedance", "quality")
branch quality < 0.5 {
  emit("alerts", {type: "low_signal_quality", sensor: "impedance"})
}

# Read multiple sensors
hypha env = {
  temperature: sense("temperature"),
  humidity: sense("humidity"),
  impedance: sense("impedance"),
  co2: sense("co2")
}
```

**Available Sensors (MycoBrain):**
| Sensor ID | Unit | Description |
|-----------|------|-------------|
| `temperature` | °C | Environmental temperature |
| `humidity` | % | Relative humidity |
| `impedance` | Ω | Mycelium electrical resistance |
| `conductivity` | µS/cm | Substrate conductivity |
| `bioelectric` | mV | Mycelium electrical potential |
| `co2` | ppm | Carbon dioxide concentration |
| `voc` | ppb | Volatile organic compounds |

---

### Signal Emission: `emit`

Send a signal to a channel (like mycelium releasing chemical signals).

**Syntax:**
```hpl
emit("channel", payload)
emit("channel", payload, "message_type")
```

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| channel | string | Target channel name |
| payload | object | Message payload |
| message_type | string | Optional: telemetry, alert, insight |

**Examples:**
```hpl
# Emit alert
emit("alerts", {
  type: "threshold_exceeded",
  sensor: "temperature",
  value: temp,
  threshold: 30
})

# Emit telemetry
emit("telemetry", {
  temperature: sense("temperature"),
  humidity: sense("humidity"),
  impedance: sense("impedance")
})

# Emit analysis insight
emit("insights", {
  health_score: 0.85,
  trend: "improving",
  recommendation: "maintain_conditions"
}, "insight")
```

---

### Conditional: `branch`

Execute code conditionally (like mycelium branching toward nutrients).

**Syntax:**
```hpl
branch condition {
  statements
}
```

**Operators:**
| Operator | Description |
|----------|-------------|
| `==` | Equal |
| `!=` | Not equal |
| `<` | Less than |
| `>` | Greater than |
| `<=` | Less than or equal |
| `>=` | Greater than or equal |

**Examples:**
```hpl
# Simple threshold check
hypha temp = sense("temperature")
branch temp > 30 {
  emit("alerts", {type: "high_temp", value: temp})
}

# Multiple conditions (nested)
hypha temp = sense("temperature")
branch temp > 35 {
  alert("critical", "Temperature critical", "temperature", 35, temp)
}
branch temp > 30 {
  branch temp <= 35 {
    alert("warning", "Temperature elevated", "temperature", 30, temp)
  }
}

# Quality-gated emission
hypha quality = sense("temperature", "quality")
branch quality >= 0.8 {
  hypha temp = sense("temperature")
  emit("telemetry", {temperature: temp, quality: quality})
}
```

---

### Data Accumulation: `grow`

Accumulate values over time (like mycelium expanding its network).

**Syntax:**
```hpl
grow name value
```

**Behavior:**
- Creates a named accumulator if it doesn't exist
- Appends the value to the accumulator
- Maintains a rolling window of last 100 values (default)
- Returns the current list of accumulated values

**Examples:**
```hpl
# Build temperature history
hypha temp = sense("temperature")
grow temp_history temp

# Use with statistical functions
hypha avg_temp = avg("temp_history")
hypha temp_trend = trend("temp_history")

# Accumulate and analyze
hypha impedance = sense("impedance")
grow impedance_readings impedance

branch stddev("impedance_readings") > 50 {
  emit("alerts", {type: "unstable_impedance", stddev: stddev("impedance_readings")})
}
```

---

### Final Output: `fruit`

Produce final output (like mycelium producing a fruiting body).

**Syntax:**
```hpl
fruit("name", value)
```

**Examples:**
```hpl
# Simple analysis result
fruit("daily_analysis", {
  avg_temp: avg("temp_history"),
  avg_humidity: avg("humidity_history"),
  health_status: "healthy"
})

# Complete report
hypha temp = sense("temperature")
hypha humidity = sense("humidity")
hypha impedance = sense("impedance")

fruit("environment_report", {
  temperature: {value: temp, trend: trend("temp_history")},
  humidity: {value: humidity, trend: trend("humidity_history")},
  impedance: {value: impedance, stability: stddev("impedance_history")},
  overall_health: 0.85,
  timestamp: now()
})
```

---

### Cleanup: `decay`

Clean up resources (like fungal decomposition).

**Syntax:**
```hpl
decay("name")
```

**Behavior:**
- Removes the named accumulator if it exists
- Removes the named variable if it exists
- Frees memory for garbage collection

**Examples:**
```hpl
# Reset history after analysis
grow temp_history temp
hypha analysis = {avg: avg("temp_history"), count: 100}
decay("temp_history")

# Conditional cleanup
branch count > 1000 {
  fruit("batch_analysis", {processed: count})
  decay("readings")
}
```

---

## Built-in Functions

### Statistical Functions

These operate on named accumulators created with `grow`:

| Function | Description | Example |
|----------|-------------|---------|
| `avg("name")` | Average of values | `hypha mean = avg("temp_history")` |
| `min_val("name")` | Minimum value | `hypha low = min_val("temp_history")` |
| `max_val("name")` | Maximum value | `hypha high = max_val("temp_history")` |
| `stddev("name")` | Standard deviation | `hypha var = stddev("temp_history")` |
| `trend("name")` | Trend direction | `hypha dir = trend("temp_history")` |

**Trend returns:**
- `"increasing"` - Values are rising
- `"decreasing"` - Values are falling
- `"stable"` - Values are steady

---

### Alert Functions

| Function | Description |
|----------|-------------|
| `alert(level, message, sensor_id, threshold, value)` | Emit an alert |
| `threshold_check(sensor_id, min, max, level)` | Check bounds |

**Alert Levels:**
- `"info"` - Informational
- `"warning"` - Attention needed
- `"critical"` - Immediate action required

**Examples:**
```hpl
# Direct alert
alert("warning", "High temperature detected", "temperature", 30, 32.5)

# Threshold checking
threshold_check("temperature", 15, 35, "warning")
threshold_check("humidity", 40, 90, "warning")
threshold_check("impedance", 500, 5000, "critical")
```

---

### Utility Functions

| Function | Description | Example |
|----------|-------------|---------|
| `now()` | Current Unix timestamp | `hypha ts = now()` |
| `elapsed("sensor")` | Seconds since last reading | `hypha age = elapsed("temperature")` |
| `log("message", "level")` | Log to console | `log("Processing complete", "info")` |

---

## Operators

### Arithmetic

| Operator | Description | Example |
|----------|-------------|---------|
| `+` | Addition | `temp + 5` |
| `-` | Subtraction | `temp - 20` |
| `*` | Multiplication | `temp * 1.8 + 32` |
| `/` | Division | `total / count` |
| `%` | Modulo | `count % 10` |

### Comparison

| Operator | Description | Example |
|----------|-------------|---------|
| `==` | Equal | `status == "active"` |
| `!=` | Not equal | `quality != 0` |
| `<` | Less than | `temp < 20` |
| `>` | Greater than | `temp > 30` |
| `<=` | Less or equal | `humidity <= 80` |
| `>=` | Greater or equal | `quality >= 0.8` |

---

## Literals

### Numbers

```hpl
hypha integer = 42
hypha float = 3.14159
hypha negative = -10.5
```

### Strings

```hpl
hypha name = "temperature"
hypha message = 'High temp alert'
```

### Objects

```hpl
hypha reading = {
  sensor: "temperature",
  value: 22.5,
  quality: 0.95,
  timestamp: now()
}
```

---

## Comments

```hpl
# This is a comment
hypha temp = sense("temperature")  # Inline comment
```

---

## Complete Examples

### Example 1: Environmental Monitoring

```hpl
# Environmental monitoring program
# Reads sensors, checks thresholds, builds history

# Read all environmental sensors
hypha temp = sense("temperature")
hypha humidity = sense("humidity")
hypha co2 = sense("co2")
hypha voc = sense("voc")

# Build history for trend analysis
grow temp_history temp
grow humidity_history humidity
grow co2_history co2

# Check temperature thresholds
branch temp > 35 {
  alert("critical", "Temperature too high", "temperature", 35, temp)
}
branch temp < 10 {
  alert("critical", "Temperature too low", "temperature", 10, temp)
}

# Check CO2 levels
branch co2 > 1500 {
  alert("warning", "CO2 elevated - ventilation needed", "co2", 1500, co2)
}

# Emit regular telemetry
emit("telemetry", {
  temperature: temp,
  humidity: humidity,
  co2: co2,
  voc: voc,
  timestamp: now()
})

# Produce analysis report
fruit("environment_analysis", {
  current: {
    temperature: temp,
    humidity: humidity,
    co2: co2,
    voc: voc
  },
  trends: {
    temperature: trend("temp_history"),
    humidity: trend("humidity_history"),
    co2: trend("co2_history")
  },
  averages: {
    temperature: avg("temp_history"),
    humidity: avg("humidity_history"),
    co2: avg("co2_history")
  }
})
```

### Example 2: Mycelium Health Monitoring

```hpl
# Mycelium health monitoring for MycoBrain devices
# Monitors bioelectric signals and impedance patterns

# Read bioelectric signals
hypha bioelectric = sense("bioelectric")
hypha impedance = sense("impedance")
hypha conductivity = sense("conductivity")

# Build signal history
grow bio_history bioelectric
grow impedance_history impedance

# Check signal quality
hypha bio_quality = sense("bioelectric", "quality")
branch bio_quality < 0.5 {
  emit("alerts", {type: "low_signal_quality", sensor: "bioelectric", quality: bio_quality})
}

# Detect impedance anomalies
hypha imp_stddev = stddev("impedance_history")
branch imp_stddev > 100 {
  emit("alerts", {
    type: "impedance_instability",
    stddev: imp_stddev,
    mean: avg("impedance_history")
  })
}

# Calculate health score
hypha stability = 1.0 - (imp_stddev / 500)
branch stability < 0 {
  hypha stability = 0
}

# Produce health report
fruit("mycelium_health", {
  bioelectric: {
    current: bioelectric,
    trend: trend("bio_history"),
    quality: bio_quality
  },
  impedance: {
    current: impedance,
    stability: stability,
    average: avg("impedance_history")
  },
  conductivity: conductivity,
  health_score: stability,
  status: branch(stability > 0.7, "healthy", "stressed")
})
```

### Example 3: Anomaly Detection

```hpl
# Anomaly detection for M-Wave earthquake precursor research
# Looks for synchronized impedance spikes across devices

# Read impedance with quality
hypha impedance = sense("impedance")
hypha quality = sense("impedance", "quality")

# Only process high-quality readings
branch quality >= 0.8 {
  grow readings impedance
  
  # Calculate statistics
  hypha mean = avg("readings")
  hypha sigma = stddev("readings")
  
  # Detect spike (> 3 sigma from mean)
  branch sigma > 0 {
    hypha zscore = (impedance - mean) / sigma
    
    branch zscore > 3 {
      emit("anomalies", {
        type: "impedance_spike",
        value: impedance,
        zscore: zscore,
        mean: mean,
        sigma: sigma,
        timestamp: now()
      }, "alert")
      
      alert("warning", "Impedance spike detected", "impedance", mean + 3 * sigma, impedance)
    }
  }
  
  # Rolling window cleanup
  branch count > 1000 {
    decay("readings")
  }
}
```

---

## Error Handling

HPL silently handles missing sensors and invalid operations:

- `sense("nonexistent")` returns `null`
- Division by zero returns `0`
- Operations on `null` propagate `null`
- Missing accumulators return `null` from statistical functions

---

## Integration

### With Mycorrhizae Protocol

HPL programs are executed by the `HPLInterpreter` class, which receives a `SensorContext` with current readings:

```python
from mycorrhizae.hpl import HPLInterpreter, SensorContext

# Create context with sensor data
context = SensorContext(device_serial="MCB-2026-0001")
context.update_sensor("temperature", 22.5, "C", quality=0.95)
context.update_sensor("humidity", 75.0, "%", quality=0.98)
context.update_sensor("impedance", 1200, "Ohm", quality=0.90)

# Execute HPL program
interpreter = HPLInterpreter(context, emit_callback=publish_to_mycorrhizae)
result = interpreter.execute(hpl_source_code)

# Access outputs
print(result["outputs"])   # List of emitted messages
print(result["alerts"])    # List of alerts
print(result["variables"]) # Final variable state
```

---

## Planned Features (Full Vision)

The following features are part of the HPL full vision as described in the [Medium article](https://medium.com/@mycosoft.inc/introduction-to-the-hypha-programming-language-hpl-069567239474). They are not yet implemented but are on the roadmap.

### Signal Pattern Language (SPL)

A sub-language within HPL for defining and working with electrical signal patterns from mycelium.

**Pattern Definition (Planned):**
```hpl
pattern GrowthSignal {
  amplitude: 0.5 - 1.0 mV;
  frequency: 0.1 - 5 Hz;
  waveform: quasi-periodic;
}

pattern EarthquakePrecursor {
  amplitude: 0.05 - 0.3 mV;
  frequency: 0.01 - 0.1 Hz;
  waveform: low-frequency-drift;
  duration: > 3600 seconds;
}
```

**Pattern Matching (Planned):**
```hpl
hypha signal = sense("bioelectric")

branch match(signal, GrowthSignal) {
  emit("insights", {type: "growth_detected", confidence: 0.85})
}

branch match(signal_history, EarthquakePrecursor) {
  alert("warning", "Possible seismic precursor", "bioelectric", 0, signal)
}
```

### Device Interface Modules (Planned)

Native modules for interacting with Mycosoft hardware:

**Mushroom 1 Module:**
```hpl
import Device.Mushroom1

Mushroom1.connect()
hypha data = Mushroom1.readSignal()
hypha status = Mushroom1.getStatus()
Mushroom1.sendStimulus(pulse_pattern)
```

**SporeBase Module:**
```hpl
import Device.Sporebase

Sporebase.connect()
Sporebase.setClimate({temperature: 25, humidity: 85})
hypha culture_status = Sporebase.getCultureHealth()
Sporebase.sendData(signalData)
```

**MycoBrain Module:**
```hpl
import Device.MycoBrain

MycoBrain.connect("192.168.0.100")
hypha bioelectric = MycoBrain.readBioelectric()
hypha environmental = MycoBrain.readEnvironment()
MycoBrain.setLED(0, 255, 0)  # Green status
```

### MINDEX Integration (Planned)

Direct integration with the Mycological Index database:

```hpl
import MINDEX

# Normalize sensor data to standard format
hypha normalizedData = MINDEX.normalize(signalData)

# Store in database
MINDEX.store(normalizedData)

# Query species characteristics
hypha species_info = MINDEX.query("species", "Pleurotus ostreatus")

# Log to experiment record
MINDEX.log("experiment-001", {
  timestamp: now(),
  reading: normalizedData,
  conditions: {temperature: temp, humidity: humidity}
})
```

### Signal Data Type (Planned)

Structured type representing electrical signals from mycelium:

```hpl
Signal {
  amplitude: float;        # Peak voltage in mV
  frequency: float;        # Dominant frequency in Hz
  phase: float;           # Phase offset in radians
  waveform: WaveformType; # sine, square, quasi-periodic, etc.
  dataPoints: array;      # Raw sample values
  quality: float;         # Signal quality 0-1
  timestamp: float;       # Unix timestamp
}

WaveformType: enum {
  SINE,
  SQUARE,
  SAWTOOTH,
  QUASI_PERIODIC,
  CHAOTIC,
  FLAT
}
```

**Usage:**
```hpl
hypha raw = sense("bioelectric")
hypha signal = Signal {
  amplitude: max_val(raw) - min_val(raw),
  frequency: dominant_frequency(raw),
  waveform: classify_waveform(raw),
  dataPoints: raw,
  quality: sense("bioelectric", "quality"),
  timestamp: now()
}
```

### Signal Processing Operators (Planned)

Advanced operators for signal analysis:

| Operator | Description | Example |
|----------|-------------|---------|
| `**` | Convolution | `signal1 ** signal2` |
| `fft()` | Fourier Transform | `hypha spectrum = fft(signal)` |
| `ifft()` | Inverse FFT | `hypha time_domain = ifft(spectrum)` |
| `filter()` | Apply filter | `hypha clean = filter(signal, "bandpass", 0.1, 50)` |
| `correlate()` | Cross-correlation | `hypha corr = correlate(signal1, signal2)` |
| `envelope()` | Amplitude envelope | `hypha env = envelope(signal)` |
| `downsample()` | Reduce sample rate | `hypha reduced = downsample(signal, 10)` |

**Example - Signal Analysis:**
```hpl
hypha raw_signal = sense("bioelectric")
hypha filtered = filter(raw_signal, "bandpass", 0.1, 50)
hypha spectrum = fft(filtered)
hypha dominant_freq = peak_frequency(spectrum)

branch dominant_freq > 10 {
  emit("alerts", {type: "high_frequency_activity", freq: dominant_freq})
}
```

### Bi-directional Fungal Communication (Planned)

Read from AND write to mycelial networks:

```hpl
# Read from mycelium
enzyme readMyceliumSignal() -> Signal {
  hypha rawSignal = Device.Mushroom1.readSignal()
  hypha processedSignal = processSignal(rawSignal)
  fruit processedSignal
}

# Write to mycelium (stimulation)
enzyme writeMyceliumSignal(signal: Signal) {
  hypha encodedSignal = encodeSignal(signal)
  Device.Mushroom1.sendSignal(encodedSignal)
}

# Response experiment
enzyme testResponse(stimulus: Signal) -> Signal {
  writeMyceliumSignal(stimulus)
  sleep(1000)  # Wait for response
  hypha response = readMyceliumSignal()
  fruit response
}
```

### Compiler and Virtual Machine (Planned)

HPL will eventually have a full compilation pipeline:

```
Source Code (.hpl)
       │
       ▼
┌─────────────────┐
│  Lexical        │  Token stream
│  Analysis       │
└─────────────────┘
       │
       ▼
┌─────────────────┐
│  Syntax         │  Abstract Syntax Tree
│  Analysis       │
└─────────────────┘
       │
       ▼
┌─────────────────┐
│  Semantic       │  Type checking, scope
│  Analysis       │
└─────────────────┘
       │
       ▼
┌─────────────────┐
│  Code           │  HPL Bytecode
│  Generation     │
└─────────────────┘
       │
       ▼
┌─────────────────┐
│  HPL Virtual    │  Execution
│  Machine        │
└─────────────────┘
```

**HPL VM Features:**
- Sandboxed execution environment
- Memory management with garbage collection
- Concurrency support for multi-device programs
- Debug interface with breakpoints and inspection

### Machine Learning Integration (Planned)

Seamless integration with ML pipelines:

```hpl
import ML

# Train on historical data
hypha model = ML.train("signal_classifier", {
  data: MINDEX.query("signals", {species: "Pleurotus ostreatus"}),
  labels: MINDEX.query("events", {type: "environmental"}),
  algorithm: "random_forest"
})

# Classify incoming signals
hypha prediction = ML.predict(model, current_signal)

branch prediction.confidence > 0.8 {
  emit("insights", {
    event_type: prediction.label,
    confidence: prediction.confidence,
    signal: current_signal
  })
}
```

### IDE Support (Planned)

Development tools for HPL:

- **Syntax Highlighting** - For VS Code, Cursor, and other editors
- **Code Completion** - Context-aware suggestions
- **Debugging Tools** - Breakpoints, step execution, variable inspection
- **Signal Visualizer** - Real-time waveform display
- **Pattern Designer** - Visual tool for creating signal patterns
- **Device Simulator** - Test without physical hardware

---

## Summary

HPL is being developed in phases:

**Phase 1 (Complete):**
- Core keywords (hypha, sense, emit, branch, grow, fruit, decay, now)
- Statistical functions (avg, min_val, max_val, stddev, trend)
- Alert functions
- Basic interpreter

**Phase 2 (In Progress):**
- Device Interface Modules
- MINDEX Integration
- FCI Hardware Driver

**Phase 3 (Planned):**
- Signal Pattern Language (SPL)
- Signal data type
- Signal processing operators

**Phase 4 (Future):**
- Full compiler + VM
- Bi-directional fungal communication
- Machine Learning integration
- IDE tools

---

## Related Documentation

- [Protocol Overview](./MYCORRHIZAE_PROTOCOL_OVERVIEW_FEB10_2026.md)
- [API Reference](./MYCORRHIZAE_API_REFERENCE_FEB10_2026.md)
- [Integration Guide](./MYCORRHIZAE_INTEGRATION_GUIDE_FEB10_2026.md)
- [Global Fungi Symbiosis Theory](./GLOBAL_FUNGI_SYMBIOSIS_THEORY_FEB10_2026.md)
- [Fungal Computer Interface](./FUNGAL_COMPUTER_INTERFACE_FEB10_2026.md)
- [HPL on Medium](https://medium.com/@mycosoft.inc/introduction-to-the-hypha-programming-language-hpl-069567239474)
