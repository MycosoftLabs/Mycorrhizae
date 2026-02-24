"""
Tests for MINDEX persistence - mindex_client and envelope format.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from mycorrhizae.message import MycorrhizaeMessage, MessageType, SourceType


class TestMINDEXClient:
    """MINDEX client and envelope format tests."""

    def test_mycorrhizae_message_to_envelope_format(self):
        """Verify MycorrhizaeMessage has structure suitable for MINDEX."""
        msg = MycorrhizaeMessage(
            channel="device.SIDE_A.telemetry",
            source_type=SourceType.DEVICE,
            source_id="SIDE_A",
            device_serial="SIDE_A",
            message_type=MessageType.TELEMETRY,
            payload={
                "pack": [
                    {"id": "ai1", "v": 1.2, "u": "V"},
                    {"id": "temp", "v": 22.5, "u": "C"},
                ]
            },
        )
        pack = msg.payload.get("pack")
        assert pack is not None
        assert isinstance(pack, list)
        assert len(pack) == 2
        assert pack[0]["id"] == "ai1"
        assert pack[0]["v"] == 1.2
        assert pack[0]["u"] == "V"

    def test_pack_dict_conversion(self):
        """Pack as dict (single reading) should convert to list for MINDEX."""
        pack_dict = {"ai1": 1.2, "temp": 22.0}
        # MINDEX expects list of {id, v, u}
        readings = [
            {"id": k, "v": v, "u": "V" if "ai" in k else "C"}
            for k, v in pack_dict.items()
        ]
        assert len(readings) == 2
        assert any(r["id"] == "ai1" and r["v"] == 1.2 for r in readings)

    @pytest.mark.asyncio
    async def test_mindex_client_persist_message_mock(self):
        """Test mindex_client.persist_message with mocked HTTP."""
        try:
            from mycorrhizae.integrations.mindex_client import MindexClient
        except ImportError:
            pytest.skip("mindex_client not available")

        client = MindexClient(base_url="http://test:8000")
        msg = MycorrhizaeMessage(
            channel="device.test.telemetry",
            source_id="test",
            payload={"pack": [{"id": "x", "v": 1, "u": "V"}]},
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_post = AsyncMock(return_value=mock_resp)
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=MagicMock(post=mock_post)
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            ok = await client.persist_message(msg)
            assert ok is True
