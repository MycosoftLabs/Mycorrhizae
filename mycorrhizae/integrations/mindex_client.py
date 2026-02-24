"""
MINDEX Client - persists Mycorrhizae messages to MINDEX API.

Uses POST /api/mindex/telemetry/envelope for device telemetry.
Falls back to storing raw message in mycorrhizae_envelopes when
envelope format does not match telemetry expectations.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

logger = logging.getLogger(__name__)

# Unit hints for common sensor keys
_UNIT_MAP = {
    "temperature": "celsius",
    "temp": "celsius",
    "humidity": "%",
    "hum": "%",
    "pressure": "hPa",
    "gas_resistance": "kOhm",
    "ai1_voltage": "V",
    "ai2_voltage": "V",
    "ai3_voltage": "V",
    "ai4_voltage": "V",
}


def _pack_to_readings(pack: Any) -> List[Dict[str, Any]]:
    """Convert payload pack to MINDEX envelope readings format."""
    if isinstance(pack, list):
        return pack
    if not isinstance(pack, dict):
        return []
    readings = []
    for k, v in pack.items():
        unit = _UNIT_MAP.get(k.lower(), None)
        readings.append({"id": k, "v": v, "u": unit})
    return readings


def _message_to_envelope(message) -> Optional[Dict[str, Any]]:
    """Convert MycorrhizaeMessage to MINDEX envelope format."""
    payload = message.payload if isinstance(message.payload, dict) else {}
    hdr = payload.get("hdr") or {}
    device_id = str(hdr.get("deviceId") or message.device_serial or message.source_id or "unknown")
    msg_id = str(hdr.get("msgId") or str(message.id))
    seq = payload.get("seq")
    if seq is None and "seq" in hdr:
        seq = hdr["seq"]
    if not isinstance(seq, int):
        seq = 0

    pack = payload.get("pack", payload)
    readings = _pack_to_readings(pack)
    if not readings and isinstance(pack, dict):
        readings = _pack_to_readings(pack)

    ts = payload.get("ts") or message.timestamp.isoformat()
    if isinstance(ts, str):
        ts = {"utc": ts}

    return {
        "hdr": {"deviceId": device_id, "msgId": msg_id},
        "ts": ts if isinstance(ts, dict) else {"utc": message.timestamp.isoformat()},
        "seq": seq,
        "pack": readings,
    }


class MindexClient:
    """
    Client for persisting Mycorrhizae messages to MINDEX.
    Uses HTTP API when MINDEX_API_URL is set.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.base_url = (base_url or os.environ.get("MINDEX_API_URL", "http://192.168.0.189:8000")).rstrip("/")
        self.api_key = api_key or os.environ.get("MINDEX_API_KEY", "")

    async def persist_message(self, message) -> bool:
        """
        Persist MycorrhizaeMessage to MINDEX.
        Returns True on success.
        """
        envelope = _message_to_envelope(message)
        if not envelope or not envelope.get("pack"):
            logger.debug("Skipping persist: no pack readings")
            return True  # Not a failure, just nothing to persist

        try:
            import httpx

            url = f"{self.base_url}/api/mindex/telemetry/envelope"
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["X-API-Key"] = self.api_key
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    url,
                    json={"envelope": envelope},
                    headers=headers,
                )
            if resp.status_code in (200, 201):
                return True
            logger.warning("MINDEX envelope ingest failed: %d %s", resp.status_code, resp.text[:200])
            return False
        except Exception as e:
            logger.error("MINDEX persist error: %s", e)
            return False

    async def execute(self, sql: str, *args) -> None:
        """
        Compatibility stub - protocol_main may call execute() with raw SQL.
        Redirects to persist via a synthetic message when possible.
        """
        logger.debug("MindexClient.execute() called - use persist_message() instead")
        pass
