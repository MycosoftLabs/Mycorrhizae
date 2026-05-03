# MMP v1 Protocol Specification

**Date:** February 23, 2026  
**Status:** Active  
**Version:** 0x02  
**Evolved from:** MDP v1

## Overview

The Mycosoft Mycorrhizae Protocol (MMP) v1 is an evolved binary protocol with a 32-byte header, truncated SHA-256 hash for integrity, and CRC-8 for quick error detection. It uses the same COBS framing as MDP v1.

## Frame Structure

### Layer 1: Raw Frame (before COBS)

| Field   | Size  | Description |
|---------|-------|-------------|
| Header  | 32 B  | MMP v1 header |
| Payload | 0..N  | JSON-encoded UTF-8 |
| Trailer | 9 B   | SHA256-truncated (8) + CRC-8 (1) |

### Layer 2: COBS Encoding

Same as MDP v1: `[code byte][COBS data][0x00]`.

## Header Layout (32 bytes)

| Offset | Size | Field       | Type   | Description |
|--------|------|-------------|--------|-------------|
| 0      | 2    | magic       | uint16 | 0x4D4D ("MM") |
| 2      | 1    | version     | uint8  | 0x02 |
| 3      | 1    | device_type | uint8  | MMPDeviceType |
| 4      | 4    | device_id   | uint32 | Device ID |
| 8      | 8    | timestamp   | uint64 | Unix ms |
| 16     | 4    | seq         | uint32 | Sequence number |
| 20     | 1    | payload_type| uint8  | MMPPayloadType |
| 21     | 1    | flags       | uint8  | MMPFlags |
| 22     | 2    | payload_len | uint16 | Payload length |
| 24     | 8    | reserved    | bytes  | Reserved |

**Struct format:** `"<HBBIQIBBH8s"` (little-endian)

## Device Types (MMPDeviceType)

| Value | Name     | Description |
|-------|----------|-------------|
| 0x01  | MYCOBRAIN| MycoBrain device |
| 0x02  | SPOREBASE| SporeBase device |
| 0x03  | FCI      | Fungal Computer Interface |
| 0x04  | GATEWAY  | Gateway |
| 0xFF  | UNKNOWN  | Unknown device |

## Payload Types (MMPPayloadType)

| Value | Name    | Description |
|-------|---------|-------------|
| 0x01  | TELEMETRY | Sensor/telemetry data |
| 0x02  | COMMAND   | Command |
| 0x03  | ACK       | Acknowledgment |
| 0x05  | EVENT     | Event |
| 0x06  | HELLO     | Handshake |
| 0x0B  | EMISSIONS | Regional/Global Emissions Data |

## Flags (MMPFlags)

| Value | Name          | Description |
|-------|---------------|-------------|
| 0x01  | ACK_REQUESTED | Sender wants ACK |
| 0x02  | IS_ACK        | This is an ACK |
| 0x04  | IS_NACK       | Negative ACK |
| 0x08  | ENCRYPTED     | Payload encrypted |
| 0x10  | PRIORITY_HIGH | High priority |

## Trailer (9 bytes)

| Field | Size | Description |
|-------|------|-------------|
| hash8 | 8 B  | First 8 bytes of SHA-256(header + payload) |
| crc8  | 1 B  | CRC-8 over (header + payload + hash8) |

**Integrity verification:**
1. Compute `h8 = SHA256(header + payload)[:8]`
2. Compute `c8 = CRC8(header + payload + h8)`
3. Compare with received trailer

### CRC-8

- **Polynomial:** 0x07  
- **Init:** 0x00  

### SHA-256 Truncated

- Full SHA-256 computed over header + payload
- First 8 bytes used for integrity

## Payload

Same JSON format as MDP v1 (telemetry, command, ACK).

## Implementation

- Python: `mycorrhizae/protocols/mmp_v1.py`, `mmp_types.py`, `mmp_crypto.py`
- Uses same COBS codec as MDP: `mdp_framing.py`
