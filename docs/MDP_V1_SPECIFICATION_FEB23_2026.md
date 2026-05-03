# MDP v1 Protocol Specification

**Date:** February 23, 2026  
**Status:** Active  
**Version:** 1.0  
**Reference:** MycoBrain firmware `mdp_hdr_v1_t`, MAS protocols

## Overview

The Mycosoft Device Protocol (MDP) v1 is a binary protocol for serial communication between MycoBrain hardware (Side-A, Side-B) and gateways. It uses COBS framing and CRC-16 for error detection.

## Frame Structure

### Layer 1: Raw Frame (before COBS)

| Field   | Size  | Description |
|---------|-------|-------------|
| Header  | 16 B  | MDP v1 header |
| Payload | 0..N  | JSON-encoded UTF-8 |
| CRC-16  | 2 B   | CRC16-CCITT-FALSE over header+payload |

### Layer 2: COBS Encoding

The raw frame is COBS-encoded. Format: `[code byte][COBS data][0x00]` (trailing delimiter only).

- No leading delimiter in stream
- Trailing `0x00` delimits each frame
- No zero bytes inside encoded data (COBS ensures this)

## Header Layout (16 bytes)

| Offset | Size | Field     | Type   | Description |
|--------|------|-----------|--------|-------------|
| 0      | 2    | magic     | uint16 | 0xA15A (MDP_MAGIC) |
| 2      | 1    | version   | uint8  | 1 (MDP_VER) |
| 3      | 1    | msg_type  | uint8  | Message type |
| 4      | 4    | seq       | uint32 | Sequence number |
| 8      | 4    | ack       | uint32 | ACK sequence (for ACK msgs) |
| 12     | 1    | flags     | uint8  | MDPFlags |
| 13     | 1    | src       | uint8  | Source endpoint |
| 14     | 1    | dst       | uint8  | Dest endpoint |
| 15     | 1    | rsv       | uint8  | Reserved |

**Struct format:** `"<HBBIIBBBB"` (little-endian)

## Message Types (MDPMessageType)

| Value | Name               | Description |
|-------|--------------------|-------------|
| 0x01  | TELEMETRY          | Sensor/telemetry data |
| 0x02  | COMMAND            | Command to device |
| 0x03  | ACK                | Acknowledgment |
| 0x05  | EVENT              | Device event |
| 0x06  | HELLO              | Handshake/hello |
| 0x07  | WIFISENSE          | WiFi sensing data |
| 0x08  | DRONE_TELEMETRY    | Drone telemetry |
| 0x09  | DRONE_MISSION_STATUS | Drone mission status |
| 0x0B  | EMISSIONS          | Global/Regional emissions tracking (CO2, CH4, Vessels) |

## Endpoints (MDPEndpoint)

| Value | Name    | Description |
|-------|---------|-------------|
| 0xA1  | SIDE_A  | MycoBrain Side-A (primary sensors) |
| 0xB1  | SIDE_B  | MycoBrain Side-B |
| 0xC0  | GATEWAY | Gateway / host |
| 0xFF  | BCAST   | Broadcast |

## Flags (MDPFlags)

| Value | Name          | Description |
|-------|---------------|-------------|
| 0x01  | ACK_REQUESTED | Sender wants ACK |
| 0x02  | IS_ACK        | This is an ACK |
| 0x04  | IS_NACK       | Negative ACK |

## CRC-16

- **Algorithm:** CRC16-CCITT-FALSE  
- **Polynomial:** 0x1021  
- **Init:** 0xFFFF  
- **Scope:** Header + payload (before CRC bytes)

## Payload

Payload is JSON-encoded UTF-8.

**Telemetry example:**
```json
{"ai1": 1.2, "ai2": 2.3, "temp": 22.5}
```

**Command example:**
```json
{"cmd": "read_sensors", "params": {}}
```

**ACK example:**
```json
{"success": true, "ack_sequence": 10}
```

## COBS Codec

- **Delimiter:** 0x00 (trailing only)
- **Max run:** 255 (0xFF)
- **Extract frames:** Split on 0x00; each `[start..0x00]` is one frame

## Implementation

- Python: `mycorrhizae/protocols/mdp_v1.py`, `mdp_types.py`, `mdp_framing.py`
- Firmware: `mycobrain/firmware/common/mdp_types.h`
