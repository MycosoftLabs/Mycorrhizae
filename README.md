# Mycorrhizae Protocol

**Data Protocol for Nature** - A pub/sub messaging protocol for routing biological sensor data through the Mycosoft ecosystem.

## Overview

The Mycorrhizae Protocol is a real-time data routing system inspired by fungal mycelium networks. It connects:

- **MycoBrain Devices** - ESP32-based sensors with FCI (Fungal Computer Interface)
- **MINDEX Database** - Canonical data layer for biological information
- **MYCA Agents** - Multi-Agent System for autonomous processing
- **NatureOS Dashboards** - Real-time visualization and control

## Features

- **Channel-based Pub/Sub** - Subscribe to specific data streams or wildcard patterns
- **API Key Authentication** - Secure access with scoped permissions and rate limiting
- **Redis-backed Streaming** - Distributed real-time message delivery
- **HPL Evaluator** - Hypha Programming Language for biological-inspired control
- **FCI Pattern Detection** - Analyze bioelectric signals from mycelium
- **M-Wave Analyzer** - Earthquake prediction via fungal signals

## Quick Start

### Docker Deployment

```bash
cd mycorrhizae-protocol
docker-compose up -d
```

### Manual Setup

```bash
# Install dependencies
pip install -e .

# Run the API server
python -m uvicorn api.main:app --host 0.0.0.0 --port 8002
```

## API Endpoints

### Health & Info

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/info` | GET | API and protocol information |
| `/api/stats` | GET | Protocol statistics |

### API Keys

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/keys` | GET | List API keys (admin) |
| `/api/keys` | POST | Create new key (admin) |
| `/api/keys/{id}` | GET | Get key details |
| `/api/keys/{id}` | DELETE | Revoke key |
| `/api/keys/{id}/rotate` | POST | Rotate key |
| `/api/keys/{id}/audit` | GET | Audit log for key |
| `/api/keys/validate` | POST | Validate a key |

### Channels

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/channels` | GET | List channels |
| `/api/channels` | POST | Create channel |
| `/api/channels/{name}` | GET | Get channel info |
| `/api/channels/{name}/publish` | POST | Publish message |

### Streaming

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/stream/subscribe` | GET | SSE stream (with channel query param) |
| `/api/stream/channels` | GET | List subscribable channels |

## Channel Naming Convention

```
device.<serial>.telemetry    - Device sensor data
device.<serial>.alerts       - Device alerts
device.<serial>.commands     - Device commands
agent.<agent_id>.tasks       - Agent task queue
agent.<agent_id>.insights    - Agent insights
aggregate.fungi.observations - Aggregated observations
system.health                - System health
alert.critical               - Critical alerts
```

### Wildcard Patterns

- `device.*.telemetry` - All device telemetry
- `device.mycelium-001.*` - All channels for a device
- `alert.#` - All alerts

## Message Format

```json
{
  "id": "uuid",
  "channel": "device.mycelium-001.telemetry",
  "timestamp": "2026-01-25T10:00:00Z",
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

## API Key Scopes

| Scope | Description |
|-------|-------------|
| `read` | Read data from APIs |
| `write` | Publish data to channels |
| `admin` | Full administrative access |
| `keys:manage` | Manage API keys |
| `channel:subscribe` | Subscribe to channels |
| `channel:publish` | Publish to channels |
| `device:read` | Read device data |
| `device:write` | Write device data |
| `etl:run` | Execute ETL pipelines |
| `agent:spawn` | Spawn MAS agents |

## Environment Variables

```env
# Database (MINDEX Postgres on 189)
MYCORRHIZAE_DATABASE_URL=postgresql://user:password@192.168.0.189:5432/mindex
MYCORRHIZAE_DB_SCHEMA=mycorrhizae

# Redis
MYCORRHIZAE_REDIS_URL=redis://192.168.0.189:6379

# One-time token for POST /api/keys/bootstrap (first admin key only)
MYCORRHIZAE_BOOTSTRAP_TOKEN=your-random-bootstrap-token

# Server
MYCORRHIZAE_HOST=0.0.0.0
MYCORRHIZAE_PORT=8002
```

## Database setup (API keys)

The key store lives in the `mycorrhizae` schema of MINDEX Postgres. Apply the migration once (it is idempotent):

```bash
psql "$MYCORRHIZAE_DATABASE_URL" -v ON_ERROR_STOP=1 -f migrations/001_api_keys_schema_OCT03_2026.sql
```

Do not point `MYCORRHIZAE_DB_SCHEMA` at `mycosoft`: MAS owns a different `mycosoft.api_keys` table in the same database.

Key lifecycle:

1. `POST /api/keys/bootstrap` with header `X-Mycorrhizae-Bootstrap-Token` mints the first admin key. It only works while the key table is empty.
2. `POST /api/keys` (admin `X-API-Key`) issues service keys (`mas`, `mindex`, `natureos`, `mycobrain`, `mycorrhizae`, `admin`). The raw key is returned once; only its SHA-256 hash is stored.
3. `POST /api/keys/validate` checks a key, its scopes and its rate limits.
4. `POST /api/keys/{id}/rotate` replaces a key; `DELETE /api/keys/{id}` revokes it. Both are written to `api_key_audit`.

## Architecture

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

## HPL (Hypha Programming Language)

A biologically-inspired DSL for processing sensor data:

```hpl
# Read sensor data
hypha temp = sense("temperature")
hypha quality = sense("impedance", "quality")

# Conditional alerting
branch temp > 30 {
  emit("alerts", {"type": "high_temp", "value": temp})
}

# Accumulate history
grow temp_history temp

# Check thresholds
threshold_check("impedance", min_val=100, max_val=5000)

# Final output
fruit("analysis", {"avg_temp": avg("temp_history")})
```

## License

MIT License - Mycosoft Labs
