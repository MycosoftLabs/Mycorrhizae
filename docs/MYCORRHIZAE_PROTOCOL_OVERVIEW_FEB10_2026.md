# Mycorrhizae Protocol Overview

**Date:** February 10, 2026  
**Version:** 1.1.0  
**Status:** Production  
**Deployment:** VM 188 (192.168.0.188:8002)

---

## Vision Statement

> **Mycorrhizae Protocol is the bridge between the biological and digital worlds—translating electrical signals from living mycelium into actionable insights that appear on NatureOS dashboards.**

---

## What is Mycorrhizae?

**Mycorrhizae Protocol** is a real-time data routing system inspired by fungal mycelium networks. Named after the symbiotic association between fungi and plant roots in nature, this protocol serves as the **bridge** between the Mycosoft hardware ecosystem (FCI devices, MycoBrain sensors) and the software ecosystem (MINDEX, NatureOS, AI agents).

**Tagline:** "Data Protocol for Nature"

### The Bridge Concept

Just as natural mycorrhizae form a symbiotic bridge between fungi and plant roots—exchanging nutrients and chemical signals—the Mycorrhizae Protocol bridges:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MYCORRHIZAE: THE BRIDGE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   BIOLOGICAL WORLD                    │         DIGITAL WORLD               │
│   ───────────────                     │         ─────────────               │
│                                       │                                     │
│   Living Mycelium                     │         NatureOS Dashboard          │
│        ↓                              │                ↑                    │
│   Bioelectric Signals                 │         Real-time Insights          │
│        ↓                              │                ↑                    │
│   FCI Electrodes                      │         AI Agent Analysis           │
│        ↓                              │                ↑                    │
│   MycoBrain Device        ──────────▶│──────────▶    MINDEX Database       │
│                           Mycorrhizae │                                     │
│   Environmental Sensors   ──────────▶│──────────▶    HPL Processing        │
│                           Protocol    │                                     │
│   Command Signals         ◀──────────│◀──────────    User Commands         │
│   (write-back)                        │                                     │
│                                       │                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### What Mycorrhizae Enables

| From Biological | Through Protocol | To Digital |
|-----------------|------------------|------------|
| Bioelectric signal from mycelium | FCI normalization → Message routing | "Growth activity detected" on dashboard |
| Environmental stress (temp/humidity) | Sensor data → Alert generation | "Optimal conditions warning" notification |
| Seismic precursor detection | M-Wave analysis → Risk scoring | "Earthquake early warning" on map |
| Chemical compound detection | VOC sensor data → Classification | "Compound identified: Psilocybin" |

### Bi-directional Communication (Vision)

The full vision includes two-way communication:

| Direction | Description | Status |
|-----------|-------------|--------|
| **Read** | Capture signals from mycelium → translate to insights | Implemented |
| **Write** | Send electrical stimulation to mycelium ← from commands | Planned |

---

## Vision vs Current Implementation

> **Note:** Mycorrhizae Protocol is being developed in phases. This document covers both what works today and the full vision.

| Feature | Current | Full Vision | Status |
|---------|---------|-------------|--------|
| Message routing (pub/sub) | Yes | Yes | **COMPLETE** |
| API key authentication | Yes | Yes | **COMPLETE** |
| Redis-backed streaming | Yes | Yes | **COMPLETE** |
| HPL processing (basic) | Yes | Yes | **COMPLETE** |
| SSE streaming | Yes | Yes | **COMPLETE** |
| FCI signal normalization | Partial | Full processing | IN PROGRESS |
| M-Wave earthquake detection | Basic | Production-ready | IN PROGRESS |
| Bi-directional fungal I/O | No | Full read/write | PLANNED |
| Pattern recognition | No | ML-based | PLANNED |
| NatureOS real-time bridge | Partial | Full integration | IN PROGRESS |

---

## Core Purpose

Mycorrhizae connects four major Mycosoft components:

```
┌─────────────────────────────────────────────────────────────────┐
│                      Mycorrhizae Protocol                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────┐    ┌─────────────┐    ┌───────────────┐          │
│   │ FCI     │───▶│ Message     │───▶│ Channel       │          │
│   │ Devices │    │ Router      │    │ Manager       │          │
│   └─────────┘    └─────────────┘    └───────────────┘          │
│                         │                   │                   │
│   ┌─────────┐           │                   │                   │
│   │ API Key │◀──────────┘                   │                   │
│   │ Validator│                              │                   │
│   └─────────┘                               │                   │
│                                             ▼                   │
│   ┌─────────┐    ┌─────────────┐    ┌───────────────┐          │
│   │ HPL     │◀───│ Redis       │◀───│ Subscribers   │          │
│   │ Evaluator│   │ Broker      │    │ (SSE/WS)      │          │
│   └─────────┘    └─────────────┘    └───────────────┘          │
│                         │                                       │
│                         ▼                                       │
│   ┌─────────────────────────────────────────────────┐          │
│   │                 MINDEX Database                  │          │
│   └─────────────────────────────────────────────────┘          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Connected Systems

| System | Role | Connection |
|--------|------|------------|
| **MycoBrain Devices** | ESP32-based sensors with FCI | Publish telemetry, receive commands |
| **MINDEX Database** | Canonical data layer | Message persistence, API key storage |
| **MYCA Agents** | Multi-Agent System | Subscribe to data, publish insights |
| **NatureOS/Website** | Dashboards | Real-time streaming via SSE |

---

## Architecture

### Core Components

| Component | File | Purpose |
|-----------|------|---------|
| **MycorrhizaeProtocol** | `mycorrhizae/protocol.py` | Central router - handles pub/sub, message routing, API key validation |
| **ChannelManager** | `mycorrhizae/channels.py` | Manages topic channels with wildcard subscriptions |
| **MycorrhizaeMessage** | `mycorrhizae/message.py` | Standardized message envelope format |
| **RedisBroker** | `mycorrhizae/broker.py` | Distributed pub/sub via Redis |
| **KeyServiceManager** | `services/key_service.py` | API key authentication, rate limiting, audit logging |

### Specialized Modules

| Module | Directory | Purpose |
|--------|-----------|---------|
| **FCI** | `mycorrhizae/fci/` | Fungal Computer Interface - bioelectric signal processing |
| **HPL** | `mycorrhizae/hpl/` | Hypha Programming Language - biological DSL |
| **M-Wave** | `mycorrhizae/mwave/` | Earthquake prediction via mycelium signals |

---

## Key Features

### 1. Channel-based Pub/Sub
- Topic-based message routing
- Wildcard subscriptions (`device.*.telemetry`, `alert.#`)
- Persistent and ephemeral channels

### 2. API Key Authentication
- SHA-256 hashed key storage
- Scoped permissions (read, write, admin, etc.)
- Rate limiting per key
- Audit logging for all operations

### 3. Redis-backed Streaming
- Distributed real-time message delivery
- Cross-process subscription
- Message buffering for offline subscribers

### 4. HPL Evaluator
- Domain-specific language for sensor processing
- Fungal metaphor keywords (hypha, branch, grow, fruit)
- Inline alerting and aggregation

### 5. FCI Pattern Detection
- Bioelectric signal normalization
- Multi-channel sensor fusion
- Quality metrics and calibration

### 6. M-Wave Analysis
- Earthquake precursor detection
- Multi-device synchronized response analysis
- Risk scoring and epicenter triangulation

### 7. NatureOS Bridge (Vision)
- Translate fungal signals to human-readable insights
- Real-time dashboard updates via WebSocket/SSE
- Voice integration with PersonaPlex
- Command interface for bi-directional communication

---

## NatureOS Integration: The Bridge in Action

Mycorrhizae Protocol's primary purpose is to bridge biological data to the NatureOS dashboard. Here's how the data flows:

### Signal-to-Insight Pipeline

```
1. SENSING
   ─────────────────────────────────────────────────────────────
   MycoBrain electrode detects 0.3mV bioelectric signal
   from oyster mushroom mycelium
   
2. CAPTURE & TRANSMISSION
   ─────────────────────────────────────────────────────────────
   FCI module on device normalizes signal
   Device publishes to: device.mycobrain-001.bioelectric
   
3. PROTOCOL ROUTING
   ─────────────────────────────────────────────────────────────
   Mycorrhizae receives message on channel
   API key validated, rate limit checked
   Message routed to subscribers:
     - MINDEX (persistence)
     - HPL evaluator (processing)
     - NatureOS SSE stream (real-time)

4. HPL PROCESSING
   ─────────────────────────────────────────────────────────────
   HPL program evaluates signal:
   
   hypha signal = sense("bioelectric")
   hypha baseline = 0.1
   
   branch signal > baseline * 3 {
     emit("insights", {
       type: "elevated_activity",
       reading: signal,
       confidence: 0.85
     })
   }

5. INSIGHT GENERATION
   ─────────────────────────────────────────────────────────────
   HPL emits insight to: agent.myca.insights
   MAS agent enriches with species data from MINDEX
   
6. NATUREOS DISPLAY
   ─────────────────────────────────────────────────────────────
   Dashboard receives via SSE:
   
   {
     "insight": "Elevated mycelium activity detected",
     "species": "Pleurotus ostreatus",
     "device": "MycoBrain #001",
     "confidence": 0.85,
     "timestamp": "2026-02-10T01:23:45Z",
     "recommendation": "Growth conditions optimal"
   }
   
   User sees: "🍄 Oyster mushroom showing elevated activity"
```

### Dashboard Integration Endpoints

NatureOS connects to Mycorrhizae for real-time updates:

| Endpoint | Purpose | Data Flow |
|----------|---------|-----------|
| `GET /api/stream/subscribe?channels=insights,alerts` | SSE stream | Protocol → Dashboard |
| `POST /api/channels/{channel}/publish` | Send commands | Dashboard → Devices |
| `GET /api/channels` | List active channels | Status info |

### Example: NatureOS Dashboard Component

```typescript
// NatureOS React component consuming Mycorrhizae stream
function FungalActivityWidget() {
  const [insights, setInsights] = useState<Insight[]>([]);
  
  useEffect(() => {
    const eventSource = new EventSource(
      `${MYCORRHIZAE_URL}/api/stream/subscribe?channels=insights`
    );
    
    eventSource.onmessage = (event) => {
      const insight = JSON.parse(event.data);
      setInsights(prev => [insight, ...prev.slice(0, 9)]);
    };
    
    return () => eventSource.close();
  }, []);
  
  return (
    <Card>
      <CardHeader>Live Fungal Activity</CardHeader>
      <CardContent>
        {insights.map(insight => (
          <InsightCard key={insight.id} insight={insight} />
        ))}
      </CardContent>
    </Card>
  );
}
```

---

## Channel Naming Convention

```
device.<serial>.telemetry    - Device sensor data
device.<serial>.alerts       - Device alerts
device.<serial>.commands     - Commands to device
agent.<agent_id>.tasks       - Agent task queue
agent.<agent_id>.insights    - Agent analysis outputs
aggregate.fungi.observations - Aggregated observations
system.health                - System health events
alert.critical               - Critical alerts
```

### Wildcard Patterns

| Pattern | Matches |
|---------|---------|
| `device.*.telemetry` | All device telemetry |
| `device.mycelium-001.*` | All channels for one device |
| `alert.#` | All alerts (multi-level wildcard) |
| `agent.*.*` | All agent channels |

---

## Message Format

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "channel": "device.mycelium-001.telemetry",
  "timestamp": "2026-02-10T01:00:00Z",
  "ttl_seconds": 3600,
  "source": {
    "type": "device",
    "id": "mycelium-001",
    "device_serial": "MCB-2026-0001"
  },
  "message_type": "telemetry",
  "payload": {
    "temperature": 22.5,
    "humidity": 75.0,
    "impedance": 1200
  },
  "tracing": {
    "correlation_id": "uuid",
    "api_key_id": "uuid"
  },
  "priority": 5,
  "tags": ["sensor", "environment"]
}
```

### Message Types

| Type | Use Case |
|------|----------|
| `telemetry` | Sensor readings |
| `alert` | Threshold violations, anomalies |
| `command` | Device control messages |
| `insight` | Agent analysis results |
| `system` | Health, status, configuration |

---

## Deployment

### Current Production

| Component | Location | Port |
|-----------|----------|------|
| Mycorrhizae API | VM 188 (192.168.0.188) | 8002 |
| PostgreSQL | VM 189 (192.168.0.189) | 5432 |
| Redis | VM 189 (192.168.0.189) | 6379 |

### Container Configuration

```yaml
# docker-compose.vm188.yml
services:
  mycorrhizae-api:
    build: .
    ports:
      - "8002:8002"
    environment:
      MYCORRHIZAE_DATABASE_URL: postgresql://mycosoft:***@192.168.0.189:5432/mindex
      MYCORRHIZAE_REDIS_URL: redis://192.168.0.189:6379
      MYCORRHIZAE_HOST: 0.0.0.0
      MYCORRHIZAE_PORT: 8002
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## Quick Start

### Health Check

```bash
curl http://192.168.0.188:8002/health
```

Response:
```json
{
  "status": "healthy",
  "database": true,
  "protocol": true,
  "timestamp": "2026-02-10T01:00:00Z"
}
```

### API Documentation

OpenAPI docs available at: http://192.168.0.188:8002/docs

---

## Related Documentation

### Protocol Documentation
- [API Reference](./MYCORRHIZAE_API_REFERENCE_FEB10_2026.md) - Complete API endpoint documentation
- [HPL Language Guide](./HPL_LANGUAGE_GUIDE_FEB10_2026.md) - Hypha Programming Language reference
- [Integration Guide](./MYCORRHIZAE_INTEGRATION_GUIDE_FEB10_2026.md) - How to integrate with MAS, MINDEX, devices

### Theoretical Foundation
- [Global Fungi Symbiosis Theory](./GLOBAL_FUNGI_SYMBIOSIS_THEORY_FEB10_2026.md) - The scientific hypothesis Mycorrhizae helps validate
- [Fungal Computer Interface](./FUNGAL_COMPUTER_INTERFACE_FEB10_2026.md) - Hardware layer for signal capture

### System Documentation
- [Vision Gap Analysis](../../MAS/mycosoft-mas/docs/VISION_VS_IMPLEMENTATION_GAP_ANALYSIS_FEB10_2026.md) - Current vs planned implementation
- [MINDEX Documentation](../../MINDEX/mindex/README.md) - Canonical data layer

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.1.0 | Feb 10, 2026 | Added NatureOS bridge concept, vision vs implementation |
| 1.0.0 | Feb 10, 2026 | Initial production deployment on VM 188 |
