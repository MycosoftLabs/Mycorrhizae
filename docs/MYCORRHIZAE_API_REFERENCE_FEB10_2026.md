# Mycorrhizae Protocol API Reference

**Date:** February 10, 2026  
**Version:** 1.0.0  
**Base URL:** `http://192.168.0.188:8002`  
**OpenAPI Docs:** `http://192.168.0.188:8002/docs`

---

## Authentication

All endpoints (except `/health` and bootstrap) require an API key in the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key" http://192.168.0.188:8002/api/channels
```

### API Key Scopes

| Scope | Permission |
|-------|------------|
| `read` | Read channels, subscribe to streams |
| `write` | Publish messages |
| `admin` | Full access including key management |
| `keys:manage` | Create, revoke, rotate keys |
| `keys:create` | Create new keys |
| `keys:revoke` | Revoke existing keys |
| `channel:create` | Create new channels |
| `channel:subscribe` | Subscribe to channels via SSE |
| `device:write` | Publish device data, send ACKs |

---

## Health & Info Endpoints

### GET /health

Health check endpoint (no authentication required).

**Response:**
```json
{
  "status": "healthy",
  "database": true,
  "protocol": true,
  "timestamp": "2026-02-10T01:00:00.000000"
}
```

**Example:**
```bash
curl http://192.168.0.188:8002/health
```

---

### GET /api/info

Get API and protocol information.

**Headers:**
- `X-API-Key`: Required

**Response:**
```json
{
  "name": "Mycorrhizae Protocol",
  "version": "1.0.0",
  "stats": {
    "channels": 5,
    "subscribers": 2,
    "messages_published": 1520,
    "messages_persisted": 1520,
    "uptime_seconds": 3600
  }
}
```

---

### GET /api/stats

Get detailed protocol statistics.

**Headers:**
- `X-API-Key`: Required

**Response:**
```json
{
  "channels": 5,
  "subscribers": 2,
  "messages_published": 1520,
  "messages_persisted": 1520,
  "uptime_seconds": 3600,
  "redis_connected": true
}
```

---

## API Key Management

### POST /api/keys/bootstrap

Create the first admin API key (bootstrap flow).

**Security Requirements:**
1. `MYCORRHIZAE_BOOTSTRAP_TOKEN` must be set in environment
2. `X-Mycorrhizae-Bootstrap-Token` header must match
3. Database must have zero existing keys

**Headers:**
- `X-Mycorrhizae-Bootstrap-Token`: Required (must match env var)

**Request Body:**
```json
{
  "name": "bootstrap-admin",
  "description": "Initial admin key",
  "rate_limit_per_minute": 600,
  "rate_limit_per_day": 50000
}
```

**Response (201):**
```json
{
  "key": "mcr_abc123...",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "key_prefix": "mcr_abc1",
  "name": "bootstrap-admin",
  "service": "admin",
  "scopes": ["admin", "keys:manage", "keys:create", "keys:revoke", "read", "write"],
  "message": "Store this key securely - it will not be shown again"
}
```

**Example:**
```bash
curl -X POST http://192.168.0.188:8002/api/keys/bootstrap \
  -H "Content-Type: application/json" \
  -H "X-Mycorrhizae-Bootstrap-Token: your-bootstrap-token" \
  -d '{"name": "bootstrap-admin"}'
```

---

### POST /api/keys

Create a new API key (requires admin).

**Headers:**
- `X-API-Key`: Required (admin scope)

**Request Body:**
```json
{
  "name": "mas-service",
  "description": "MAS Multi-Agent System access",
  "service": "mas",
  "scopes": ["read", "write", "channel:subscribe"],
  "rate_limit_per_minute": 60,
  "rate_limit_per_day": 10000,
  "expires_in_days": 365
}
```

**Service Options:**
- `mycorrhizae`, `mindex`, `natureos`, `mycobrain`, `mas`, `admin`

**Response (201):**
```json
{
  "key": "mcr_xyz789...",
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "key_prefix": "mcr_xyz7",
  "name": "mas-service",
  "service": "mas",
  "scopes": ["read", "write", "channel:subscribe"],
  "message": "Store this key securely - it will not be shown again"
}
```

**Example:**
```bash
curl -X POST http://192.168.0.188:8002/api/keys \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-admin-key" \
  -d '{
    "name": "device-gateway",
    "service": "mycobrain",
    "scopes": ["read", "write", "device:write"]
  }'
```

---

### GET /api/keys

List all API keys (admin only).

**Headers:**
- `X-API-Key`: Required (admin scope)

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `service` | string | null | Filter by service |
| `include_inactive` | bool | false | Include revoked keys |
| `limit` | int | 100 | Max results |
| `offset` | int | 0 | Pagination offset |

**Response (200):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "key_prefix": "mcr_abc1",
    "name": "bootstrap-admin",
    "description": null,
    "service": "admin",
    "scopes": ["admin", "keys:manage", "read", "write"],
    "rate_limit_per_minute": 600,
    "rate_limit_per_day": 50000,
    "expires_at": null,
    "last_used_at": "2026-02-10T01:00:00",
    "usage_count": 150,
    "is_active": true,
    "created_at": "2026-02-10T00:00:00"
  }
]
```

---

### GET /api/keys/{key_id}

Get details for a specific key.

**Headers:**
- `X-API-Key`: Required (admin scope)

**Response (200):** Same format as list item

---

### POST /api/keys/{key_id}/rotate

Rotate an API key (creates new, deactivates old).

**Headers:**
- `X-API-Key`: Required (admin scope)

**Query Parameters:**
- `reason` (optional): Reason for rotation

**Response (200):**
```json
{
  "new_key": "mcr_new123...",
  "new_key_id": "770e8400-e29b-41d4-a716-446655440002",
  "old_key_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Old key has been deactivated. Store new key securely."
}
```

---

### DELETE /api/keys/{key_id}

Revoke (deactivate) an API key.

**Headers:**
- `X-API-Key`: Required (admin scope)

**Query Parameters:**
- `reason` (optional): Reason for revocation

**Response (200):**
```json
{
  "status": "revoked",
  "key_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### POST /api/keys/validate

Validate an API key (no admin required).

**Request Body:**
```json
{
  "key": "mcr_abc123...",
  "required_scopes": ["read", "write"]
}
```

**Response (200):**
```json
{
  "valid": true,
  "error": null,
  "key_id": "550e8400-e29b-41d4-a716-446655440000",
  "service": "admin",
  "scopes": ["admin", "read", "write"],
  "remaining_minute": 58,
  "remaining_day": 9850
}
```

---

### GET /api/keys/{key_id}/audit

Get audit log for a key.

**Headers:**
- `X-API-Key`: Required (admin scope)

**Query Parameters:**
- `action` (optional): Filter by action type
- `limit` (optional, default 100): Max results

**Response (200):**
```json
[
  {
    "id": 1,
    "key_id": "550e8400-e29b-41d4-a716-446655440000",
    "action": "validate",
    "ip_address": "192.168.0.188",
    "user_agent": "python-requests/2.28.0",
    "endpoint": "/api/channels",
    "created_at": "2026-02-10T01:00:00"
  }
]
```

---

## Channel Management

### GET /api/channels

List all channels.

**Headers:**
- `X-API-Key`: Required

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `type` | string | Filter by channel type |
| `prefix` | string | Filter by name prefix |

**Response (200):**
```json
[
  {
    "name": "device.mycelium-001.telemetry",
    "type": "device",
    "description": "MycoBrain device telemetry",
    "required_scopes": ["read"],
    "write_scopes": ["write"],
    "message_count": 1520,
    "subscriber_count": 2,
    "last_message_at": "2026-02-10T01:00:00",
    "created_at": "2026-02-09T12:00:00",
    "persist_messages": true,
    "ttl_seconds": 3600,
    "tags": ["sensor", "environment"]
  }
]
```

**Example:**
```bash
curl -H "X-API-Key: your-key" \
  "http://192.168.0.188:8002/api/channels?type=device&prefix=device.mycelium"
```

---

### POST /api/channels

Create a new channel.

**Headers:**
- `X-API-Key`: Required (admin or channel:create scope)

**Request Body:**
```json
{
  "name": "device.mycelium-002.telemetry",
  "type": "device",
  "description": "New MycoBrain device",
  "required_scopes": ["read"],
  "write_scopes": ["write", "device:write"],
  "persist_messages": true,
  "ttl_seconds": 3600,
  "tags": ["sensor", "mycobrain"]
}
```

**Response (201):** Same format as GET response item

---

### GET /api/channels/{channel_name}

Get a specific channel.

**Headers:**
- `X-API-Key`: Required

**Response (200):** Same format as list item

---

### POST /api/channels/{channel_name}/publish

Publish a message to a channel.

**Headers:**
- `X-API-Key`: Required (write scope)

**Request Body:**
```json
{
  "payload": {
    "temperature": 22.5,
    "humidity": 75.0,
    "impedance": 1200,
    "timestamp": "2026-02-10T01:00:00Z"
  },
  "message_type": "telemetry",
  "source_id": "mycelium-001",
  "device_serial": "MCB-2026-0001",
  "priority": 5,
  "tags": ["sensor", "environment"]
}
```

**Message Types:**
- `telemetry` - Sensor readings
- `alert` - Threshold violations
- `command` - Device commands
- `insight` - Agent analysis
- `event` - Generic events
- `system` - System messages

**Response (200):**
```json
{
  "message_id": "550e8400-e29b-41d4-a716-446655440000",
  "channel": "device.mycelium-001.telemetry",
  "subscribers_notified": 2,
  "persisted": true
}
```

**Example:**
```bash
curl -X POST http://192.168.0.188:8002/api/channels/device.mycelium-001.telemetry/publish \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "payload": {"temperature": 22.5, "humidity": 75.0},
    "message_type": "telemetry"
  }'
```

---

## Streaming (Server-Sent Events)

### GET /api/stream/subscribe

Subscribe to a channel via SSE (Server-Sent Events).

**Headers:**
- `X-API-Key`: Required (read, channel:subscribe scope)

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `channel` | string | Channel pattern (supports wildcards) |

**Wildcard Patterns:**
- `device.*.telemetry` - All device telemetry
- `device.mycelium-001.*` - All channels for one device
- `alert.#` - All alerts (multi-level)

**SSE Events:**

1. **connected** - Initial connection confirmation
```json
{"subscription_id": "uuid", "channel_pattern": "device.*.telemetry"}
```

2. **message** - Incoming messages
```json
{
  "id": "uuid",
  "channel": "device.mycelium-001.telemetry",
  "timestamp": "2026-02-10T01:00:00Z",
  "payload": {"temperature": 22.5},
  "message_type": "telemetry"
}
```

3. **ping** - Keepalive (every 30 seconds)
```json
{"ts": 1707526800.123}
```

**Example (curl):**
```bash
curl -N -H "X-API-Key: your-key" \
  "http://192.168.0.188:8002/api/stream/subscribe?channel=device.*.telemetry"
```

**Example (JavaScript):**
```javascript
const eventSource = new EventSource(
  'http://192.168.0.188:8002/api/stream/subscribe?channel=device.*.telemetry',
  { headers: { 'X-API-Key': 'your-key' } }
);

eventSource.addEventListener('connected', (e) => {
  console.log('Connected:', JSON.parse(e.data));
});

eventSource.addEventListener('message', (e) => {
  const msg = JSON.parse(e.data);
  console.log('Received:', msg.channel, msg.payload);
});
```

**Example (Python):**
```python
import requests

response = requests.get(
    "http://192.168.0.188:8002/api/stream/subscribe",
    params={"channel": "device.*.telemetry"},
    headers={"X-API-Key": "your-key"},
    stream=True,
)

for line in response.iter_lines():
    if line:
        print(line.decode())
```

---

### GET /api/stream/channels

List channels available for subscription.

**Headers:**
- `X-API-Key`: Required

**Response (200):**
```json
{
  "channels": [
    "device.mycelium-001.telemetry",
    "device.mycelium-002.telemetry",
    "system.health"
  ],
  "count": 3,
  "patterns": [
    "device.*.telemetry",
    "device.*.alerts",
    "agent.*.tasks",
    "aggregate.*",
    "system.*"
  ]
}
```

---

### POST /api/stream/replay/ack

Acknowledge a replayed message (for exactly-once delivery).

**Headers:**
- `X-API-Key`: Required (write, device:write scope)

**Request Body:**
```json
{
  "device_id": "mycelium-001",
  "msg_id": "550e8400-e29b-41d4-a716-446655440000",
  "seq": 42,
  "accepted": true,
  "reason": null
}
```

**Response (200):**
```json
{
  "device_id": "mycelium-001",
  "msg_id": "550e8400-e29b-41d4-a716-446655440000",
  "seq": 42,
  "accepted": true,
  "ack_ts": "2026-02-10T01:00:00Z"
}
```

---

## Error Responses

All endpoints return standard HTTP error codes:

| Code | Meaning |
|------|---------|
| 400 | Bad Request - Invalid input |
| 403 | Forbidden - Invalid or insufficient API key |
| 404 | Not Found - Resource doesn't exist |
| 409 | Conflict - Resource already exists |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |
| 503 | Service Unavailable - Database or protocol not ready |

**Error Response Format:**
```json
{
  "detail": "Error message describing the issue"
}
```

---

## Rate Limiting

Rate limits are enforced per API key:

- **Per minute**: Configured when key is created (default: 60)
- **Per day**: Configured when key is created (default: 10,000)

When rate limited, the API returns 429 with remaining limits in the response:

```json
{
  "detail": "Rate limit exceeded",
  "remaining_minute": 0,
  "remaining_day": 5000,
  "retry_after": 60
}
```

---

## Related Documentation

- [Protocol Overview](./MYCORRHIZAE_PROTOCOL_OVERVIEW_FEB10_2026.md)
- [HPL Language Guide](./HPL_LANGUAGE_GUIDE_FEB10_2026.md)
- [Integration Guide](./MYCORRHIZAE_INTEGRATION_GUIDE_FEB10_2026.md)
