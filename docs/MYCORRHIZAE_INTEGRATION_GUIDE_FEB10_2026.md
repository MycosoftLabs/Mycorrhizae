# Mycorrhizae Integration Guide

**Date:** February 10, 2026  
**Version:** 1.0.0  
**Deployment:** VM 188 (192.168.0.188:8002)

---

## Overview

This guide covers integrating Mycorrhizae Protocol with the major Mycosoft systems:

1. **MAS (Multi-Agent System)** - Agent-to-agent communication
2. **MINDEX** - Data persistence and querying
3. **MycoBrain Devices** - IoT sensor data ingestion
4. **NatureOS/Website** - Real-time dashboards

---

## Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│                          MYCOSOFT ECOSYSTEM                            │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│   ┌─────────────┐     ┌──────────────────┐     ┌─────────────┐        │
│   │  MycoBrain  │────▶│   Mycorrhizae    │◀───▶│    MAS      │        │
│   │  Devices    │     │   Protocol       │     │  Agents     │        │
│   │  (FCI)      │     │   (192.168.0.188:8002)│  (192.168.0.188:8001)│
│   └─────────────┘     └────────┬─────────┘     └─────────────┘        │
│                                │                                       │
│           ┌────────────────────┼────────────────────┐                  │
│           ▼                    ▼                    ▼                  │
│   ┌─────────────┐     ┌──────────────┐     ┌─────────────┐            │
│   │   Redis     │     │   MINDEX     │     │  NatureOS   │            │
│   │   Pub/Sub   │     │  PostgreSQL  │     │  Dashboard  │            │
│   │  (189:6379) │     │  (189:5432)  │     │  (SSE)      │            │
│   └─────────────┘     └──────────────┘     └─────────────┘            │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 1. MAS Integration

### Overview

MYCA agents communicate with Mycorrhizae for:
- Publishing analysis results and insights
- Subscribing to device telemetry streams
- Receiving task assignments via channels
- Coordinating between agents

### Configuration

MAS requires these environment variables:

```bash
MYCORRHIZAE_API_URL=http://192.168.0.188:8002
MYCORRHIZAE_API_KEY=mcr_your_api_key_here
```

### Agent-to-Mycorrhizae Communication

#### Publishing Agent Insights

```python
import httpx

class MyAgent:
    def __init__(self):
        self.mycorrhizae_url = os.getenv("MYCORRHIZAE_API_URL")
        self.api_key = os.getenv("MYCORRHIZAE_API_KEY")
    
    async def publish_insight(self, insight: dict):
        """Publish an analysis insight to Mycorrhizae."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.mycorrhizae_url}/api/channels/agent.{self.agent_id}.insights/publish",
                headers={"X-API-Key": self.api_key},
                json={
                    "payload": insight,
                    "message_type": "insight",
                    "source_id": self.agent_id,
                    "tags": ["analysis", "mycelium"]
                }
            )
            return response.json()
```

#### Subscribing to Device Telemetry

```python
import httpx

async def subscribe_to_devices():
    """Subscribe to all device telemetry via SSE."""
    url = f"{MYCORRHIZAE_URL}/api/stream/subscribe"
    
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "GET",
            url,
            params={"channel": "device.*.telemetry"},
            headers={"X-API-Key": API_KEY},
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    data = json.loads(line[5:])
                    await process_telemetry(data)
```

### Agent Channel Patterns

| Channel | Purpose |
|---------|---------|
| `agent.{id}.tasks` | Incoming task queue |
| `agent.{id}.insights` | Outgoing analysis results |
| `agent.{id}.status` | Agent health/status |
| `agent.{id}.commands` | Control commands |

---

## 2. MINDEX Integration

### Overview

MINDEX is the canonical data layer. Mycorrhizae persists messages to MINDEX tables.

### Database Schema

Mycorrhizae uses these tables in MINDEX:

```sql
-- Message persistence
CREATE TABLE mycorrhizae_messages (
    id UUID PRIMARY KEY,
    channel VARCHAR(200) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    source_type VARCHAR(50),
    source_id VARCHAR(100),
    device_serial VARCHAR(100),
    message_type VARCHAR(50),
    payload JSONB,
    api_key_id UUID REFERENCES api_keys(id),
    correlation_id UUID,
    ttl_seconds INTEGER DEFAULT 3600,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- API keys (shared with Mycorrhizae)
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_hash VARCHAR(64) NOT NULL,
    key_prefix VARCHAR(12) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    service VARCHAR(50) NOT NULL,
    scopes JSONB DEFAULT '["read"]',
    rate_limit_per_minute INTEGER DEFAULT 60,
    rate_limit_per_day INTEGER DEFAULT 10000,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);
```

### Connection Configuration

Mycorrhizae connects to MINDEX via:

```bash
MYCORRHIZAE_DATABASE_URL=postgresql://mycosoft:password@192.168.0.189:5432/mindex
MYCORRHIZAE_REDIS_URL=redis://192.168.0.189:6379
```

### Querying Mycorrhizae Data from MINDEX

```python
import asyncpg

async def get_device_history(device_serial: str, hours: int = 24):
    """Query message history for a device."""
    conn = await asyncpg.connect(MINDEX_DATABASE_URL)
    
    rows = await conn.fetch("""
        SELECT id, timestamp, message_type, payload
        FROM mycorrhizae_messages
        WHERE device_serial = $1
          AND timestamp > NOW() - INTERVAL '$2 hours'
        ORDER BY timestamp DESC
        LIMIT 1000
    """, device_serial, hours)
    
    await conn.close()
    return [dict(r) for r in rows]
```

---

## 3. MycoBrain Device Integration

### Overview

MycoBrain devices (ESP32-based) send sensor data through Mycorrhizae via:
- Direct HTTP POST to `/api/channels/{channel}/publish`
- Via LoRaWAN gateway forwarding
- Via MQTT bridge

### Device Message Format

Devices should publish in the IoT envelope format:

```json
{
  "hdr": {
    "device_id": "MCB-2026-0001",
    "ts": 1707526800000,
    "seq": 42,
    "fw": "1.2.3"
  },
  "body": {
    "temperature": 22.5,
    "humidity": 75.0,
    "impedance": 1200,
    "conductivity": 850,
    "bioelectric": -15.3
  },
  "hash": "sha256:abc123...",
  "sig": "base64-ed25519-signature"
}
```

### ESP32 Code Example (Arduino)

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

const char* MYCORRHIZAE_URL = "http://192.168.0.188:8002";
const char* API_KEY = "mcr_device_key_here";
const char* DEVICE_ID = "MCB-2026-0001";

void publishTelemetry(float temp, float humidity, float impedance) {
    HTTPClient http;
    
    String channel = String("device.") + DEVICE_ID + ".telemetry";
    String url = String(MYCORRHIZAE_URL) + "/api/channels/" + channel + "/publish";
    
    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("X-API-Key", API_KEY);
    
    StaticJsonDocument<512> doc;
    doc["message_type"] = "telemetry";
    doc["device_serial"] = DEVICE_ID;
    
    JsonObject payload = doc.createNestedObject("payload");
    payload["temperature"] = temp;
    payload["humidity"] = humidity;
    payload["impedance"] = impedance;
    payload["timestamp"] = millis();
    
    String body;
    serializeJson(doc, body);
    
    int responseCode = http.POST(body);
    
    if (responseCode == 200) {
        Serial.println("Telemetry published successfully");
    } else {
        Serial.printf("Publish failed: %d\n", responseCode);
    }
    
    http.end();
}

void loop() {
    float temp = readTemperature();
    float humidity = readHumidity();
    float impedance = readImpedance();
    
    publishTelemetry(temp, humidity, impedance);
    
    delay(10000); // Every 10 seconds
}
```

### Python Gateway Example

For LoRa or MQTT gateways forwarding to Mycorrhizae:

```python
import httpx
import json

class MycorrhizaeGateway:
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key
        self.client = httpx.AsyncClient()
    
    async def forward_device_message(self, device_serial: str, readings: dict):
        """Forward device readings to Mycorrhizae."""
        channel = f"device.{device_serial}.telemetry"
        
        response = await self.client.post(
            f"{self.api_url}/api/channels/{channel}/publish",
            headers={
                "X-API-Key": self.api_key,
                "Content-Type": "application/json",
            },
            json={
                "payload": readings,
                "message_type": "telemetry",
                "device_serial": device_serial,
                "tags": ["gateway", "forwarded"],
            }
        )
        
        return response.json()
    
    async def send_command_to_device(self, device_serial: str, command: dict):
        """Send a command to a device."""
        channel = f"device.{device_serial}.commands"
        
        response = await self.client.post(
            f"{self.api_url}/api/channels/{channel}/publish",
            headers={
                "X-API-Key": self.api_key,
                "Content-Type": "application/json",
            },
            json={
                "payload": command,
                "message_type": "command",
            }
        )
        
        return response.json()
```

### FCI (Fungal Computer Interface) Integration

The FCI module processes bioelectric signals from mycelium networks:

```python
from mycorrhizae.fci import FCIInterface, FCISignalType

# Initialize FCI for a device
fci = FCIInterface(device_serial="MCB-2026-0001")

# Record readings from sensors
fci.record_reading("bioelectric_1", raw_value=-15.3, quality=0.95)
fci.record_reading("impedance", raw_value=1200.0, quality=0.90)
fci.record_reading("temperature", raw_value=22.5, quality=0.98)

# Get aggregated stats
stats = fci.get_aggregate_stats()

# Convert to Mycorrhizae message payload
payload = fci.to_mycorrhizae_payload()
await gateway.forward_device_message("MCB-2026-0001", payload)
```

---

## 4. NatureOS/Website Integration

### Overview

The website and NatureOS consume Mycorrhizae streams for real-time dashboards.

### SSE Streaming (JavaScript/React)

```typescript
// lib/mycorrhizae/client.ts
export class MycorrhizaeClient {
  private eventSource: EventSource | null = null;
  private apiUrl: string;
  private apiKey: string;

  constructor(apiUrl: string, apiKey: string) {
    this.apiUrl = apiUrl;
    this.apiKey = apiKey;
  }

  subscribe(
    channelPattern: string,
    onMessage: (data: any) => void,
    onError?: (error: Event) => void
  ): void {
    const url = new URL(`${this.apiUrl}/api/stream/subscribe`);
    url.searchParams.set('channel', channelPattern);
    
    // Note: SSE doesn't support custom headers in browser
    // API key must be passed as query param or via cookie
    url.searchParams.set('api_key', this.apiKey);
    
    this.eventSource = new EventSource(url.toString());
    
    this.eventSource.addEventListener('connected', (e) => {
      console.log('Connected to Mycorrhizae stream');
    });
    
    this.eventSource.addEventListener('message', (e) => {
      const data = JSON.parse(e.data);
      onMessage(data);
    });
    
    this.eventSource.addEventListener('ping', () => {
      console.log('Keepalive received');
    });
    
    this.eventSource.onerror = onError || console.error;
  }

  unsubscribe(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }
}
```

### React Hook for Real-time Data

```tsx
// hooks/useMycorrhizaeStream.ts
import { useEffect, useState, useCallback } from 'react';
import { MycorrhizaeClient } from '@/lib/mycorrhizae/client';

interface MycorrhizaeMessage {
  id: string;
  channel: string;
  timestamp: string;
  payload: Record<string, any>;
}

export function useMycorrhizaeStream(channelPattern: string) {
  const [messages, setMessages] = useState<MycorrhizaeMessage[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const client = new MycorrhizaeClient(
      process.env.NEXT_PUBLIC_MYCORRHIZAE_URL!,
      process.env.NEXT_PUBLIC_MYCORRHIZAE_KEY!
    );

    client.subscribe(
      channelPattern,
      (data) => {
        setMessages((prev) => [...prev.slice(-99), data]);
        setConnected(true);
      },
      (e) => {
        setError('Connection lost');
        setConnected(false);
      }
    );

    return () => client.unsubscribe();
  }, [channelPattern]);

  const clear = useCallback(() => setMessages([]), []);

  return { messages, connected, error, clear };
}
```

### Dashboard Component Example

```tsx
// components/device-monitor.tsx
'use client';

import { useMycorrhizaeStream } from '@/hooks/useMycorrhizaeStream';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function DeviceMonitor({ deviceSerial }: { deviceSerial: string }) {
  const { messages, connected } = useMycorrhizaeStream(
    `device.${deviceSerial}.telemetry`
  );

  const latest = messages[messages.length - 1];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Device: {deviceSerial}
          <span className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
        </CardTitle>
      </CardHeader>
      <CardContent>
        {latest ? (
          <div className="grid grid-cols-3 gap-4">
            <div>
              <div className="text-sm text-muted-foreground">Temperature</div>
              <div className="text-2xl font-bold">{latest.payload.temperature}°C</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Humidity</div>
              <div className="text-2xl font-bold">{latest.payload.humidity}%</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Impedance</div>
              <div className="text-2xl font-bold">{latest.payload.impedance}Ω</div>
            </div>
          </div>
        ) : (
          <div className="text-muted-foreground">Waiting for data...</div>
        )}
      </CardContent>
    </Card>
  );
}
```

### Next.js API Route Proxy

For server-side Mycorrhizae access:

```typescript
// app/api/mycorrhizae/channels/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const response = await fetch(
    `${process.env.MYCORRHIZAE_API_URL}/api/channels`,
    {
      headers: {
        'X-API-Key': process.env.MYCORRHIZAE_API_KEY!,
      },
    }
  );

  const data = await response.json();
  return NextResponse.json(data);
}
```

---

## 5. M-Wave Earthquake Prediction Integration

### Overview

M-Wave uses distributed mycelium sensors for earthquake precursor detection.

### Analyzer Usage

```python
from mycorrhizae.mwave import MWaveAnalyzer, MWaveReading

# Create analyzer centered on sensor network
analyzer = MWaveAnalyzer(location=(37.7749, -122.4194))

# Add readings from multiple devices
for device_data in incoming_readings:
    reading = MWaveReading(
        device_serial=device_data["device_id"],
        latitude=device_data["lat"],
        longitude=device_data["lon"],
        impedance_ohm=device_data["impedance"],
        conductivity_us=device_data["conductivity"],
        soil_moisture=device_data["moisture"],
        temperature_c=device_data["temp"],
    )
    analyzer.add_reading(reading)

# Analyze for anomalies
results = analyzer.analyze(window_minutes=60)

print(f"Risk Level: {results['risk_level']}")
print(f"Anomalies Found: {len(results['anomalies'])}")

# Predict epicenter if anomalies detected
if results["anomalies"]:
    epicenter = analyzer.predict_epicenter(results["anomalies"])
    if epicenter:
        print(f"Estimated epicenter: {epicenter['estimated_latitude']}, {epicenter['estimated_longitude']}")
        print(f"Confidence: {epicenter['confidence']:.2%}")
```

### Publishing M-Wave Alerts

```python
async def publish_mwave_alert(analyzer: MWaveAnalyzer):
    """Publish M-Wave analysis to Mycorrhizae."""
    results = analyzer.analyze(window_minutes=60)
    
    if results["risk_level"] in ("elevated", "high", "critical"):
        await gateway.client.post(
            f"{MYCORRHIZAE_URL}/api/channels/alert.mwave.seismic/publish",
            headers={"X-API-Key": API_KEY},
            json={
                "payload": {
                    "risk_level": results["risk_level"],
                    "risk_score": results["risk_score"],
                    "anomaly_count": len(results["anomalies"]),
                    "anomalies": results["anomalies"],
                    "epicenter_estimate": analyzer.predict_epicenter(results["anomalies"]),
                },
                "message_type": "alert",
                "priority": 1 if results["risk_level"] == "critical" else 3,
                "tags": ["mwave", "seismic", results["risk_level"]],
            }
        )
```

---

## 6. HPL Integration

### Overview

HPL (Hypha Programming Language) programs process sensor data with biological metaphors.

### Running HPL from MAS Agent

```python
from mycorrhizae.hpl import HPLInterpreter, SensorContext

async def process_device_with_hpl(device_serial: str, readings: dict, hpl_program: str):
    """Process device readings through an HPL program."""
    
    # Create sensor context
    context = SensorContext(device_serial=device_serial)
    for sensor_id, value in readings.items():
        context.update_sensor(sensor_id, value["value"], value["unit"], value.get("quality", 1.0))
    
    # Define emit callback to publish to Mycorrhizae
    async def emit_callback(output: dict):
        await mycorrhizae_client.publish_message(
            channel=output["channel"],
            payload=output["payload"],
            message_type=output["message_type"],
        )
    
    # Run HPL program
    interpreter = HPLInterpreter(context, emit_callback=emit_callback)
    result = interpreter.execute(hpl_program)
    
    return result
```

### Example HPL Program for Device Monitoring

```hpl
# Device Health Monitor
# Monitors environmental conditions and mycelium health

hypha temp = sense("temperature")
hypha humidity = sense("humidity")
hypha impedance = sense("impedance")
hypha bioelectric = sense("bioelectric")

# Build history for trend analysis
grow temp_history temp
grow impedance_history impedance

# Check environmental bounds
branch temp > 35 {
  alert("critical", "Temperature too high", "temperature", 35, temp)
}
branch temp < 10 {
  alert("critical", "Temperature too low", "temperature", 10, temp)
}

# Check impedance stability
hypha imp_std = stddev("impedance_history")
branch imp_std > 100 {
  emit("alerts", {
    type: "impedance_instability",
    stddev: imp_std,
    mean: avg("impedance_history")
  })
}

# Calculate health score
hypha health = 1.0
branch temp > 30 {
  hypha health = health - 0.2
}
branch humidity < 50 {
  hypha health = health - 0.2
}
branch imp_std > 50 {
  hypha health = health - 0.3
}

# Output comprehensive telemetry
emit("telemetry", {
  temperature: temp,
  humidity: humidity,
  impedance: impedance,
  bioelectric: bioelectric,
  trends: {
    temperature: trend("temp_history"),
    impedance: trend("impedance_history")
  },
  health_score: health
})

# Produce final health report
fruit("health_report", {
  device: "current",
  score: health,
  status: branch(health > 0.7, "healthy", "stressed"),
  readings_processed: 1,
  timestamp: now()
})
```

---

## 7. API Key Management

### Creating Keys for Integrations

```bash
# Create key for MAS service
curl -X POST http://192.168.0.188:8002/api/keys \
  -H "X-API-Key: admin-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "mas-orchestrator",
    "service": "mas",
    "scopes": ["read", "write", "channel:subscribe", "channel:publish"],
    "rate_limit_per_minute": 300,
    "rate_limit_per_day": 100000
  }'

# Create key for device gateway
curl -X POST http://192.168.0.188:8002/api/keys \
  -H "X-API-Key: admin-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "device-gateway",
    "service": "mycobrain",
    "scopes": ["read", "write", "device:write"],
    "rate_limit_per_minute": 600,
    "rate_limit_per_day": 500000
  }'

# Create key for website dashboard
curl -X POST http://192.168.0.188:8002/api/keys \
  -H "X-API-Key: admin-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "website-dashboard",
    "service": "natureos",
    "scopes": ["read", "channel:subscribe"],
    "rate_limit_per_minute": 120,
    "rate_limit_per_day": 50000
  }'
```

### Recommended Scopes by Integration

| Integration | Scopes |
|-------------|--------|
| MAS Agents | `read`, `write`, `channel:subscribe`, `channel:publish` |
| Device Gateway | `read`, `write`, `device:write` |
| Website Dashboard | `read`, `channel:subscribe` |
| Admin Tools | `admin`, `keys:manage`, `read`, `write` |
| M-Wave Analyzer | `read`, `write`, `channel:publish` |

---

## 8. Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 403 Forbidden | Invalid or missing API key | Check `X-API-Key` header |
| 403 Missing scope | Key lacks required permission | Add scope or use different key |
| 429 Rate limited | Too many requests | Implement backoff, increase limits |
| 404 Channel not found | Non-device channel doesn't exist | Create channel first |
| 503 Service unavailable | Database or Redis down | Check VM 189 services |

### Retry Logic

```python
import asyncio
import httpx

async def publish_with_retry(
    url: str,
    data: dict,
    headers: dict,
    max_retries: int = 3,
    backoff: float = 1.0,
):
    """Publish with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, headers=headers)
                
                if response.status_code == 429:
                    # Rate limited - use Retry-After if available
                    retry_after = int(response.headers.get("Retry-After", backoff * (2 ** attempt)))
                    await asyncio.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(backoff * (2 ** attempt))
    
    raise Exception("Max retries exceeded")
```

---

## 9. Health Checks

### Checking Mycorrhizae Health

```bash
# Basic health check
curl http://192.168.0.188:8002/health

# Expected response
{
  "status": "healthy",
  "database": true,
  "protocol": true,
  "timestamp": "2026-02-10T12:00:00.000000"
}
```

### Monitoring Script

```python
#!/usr/bin/env python3
"""Monitor Mycorrhizae health."""
import httpx
import asyncio

async def check_health():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://192.168.0.188:8002/health")
            data = response.json()
            
            if data["status"] == "healthy":
                print("✓ Mycorrhizae is healthy")
                return True
            else:
                print(f"! Mycorrhizae is degraded: {data}")
                return False
                
    except Exception as e:
        print(f"✗ Mycorrhizae is down: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(check_health())
```

---

## Related Documentation

- [Protocol Overview](./MYCORRHIZAE_PROTOCOL_OVERVIEW_FEB10_2026.md)
- [API Reference](./MYCORRHIZAE_API_REFERENCE_FEB10_2026.md)
- [HPL Language Guide](./HPL_LANGUAGE_GUIDE_FEB10_2026.md)
