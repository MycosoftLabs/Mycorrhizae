"""
Serial Handler - reads/writes MDP/MMP frames over serial port.

Uses COBS framing to extract complete frames from a byte stream.
"""

from __future__ import annotations

import asyncio
import logging
from typing import AsyncIterator, Callable, Optional

from ..protocols.mdp_framing import COBSCodec

logger = logging.getLogger(__name__)


class SerialHandler:
    """
    Handles serial port I/O with COBS frame extraction.
    Buffers incoming bytes and yields complete COBS-encoded frames.
    """

    def __init__(
        self,
        port: str = "COM7",
        baudrate: int = 115200,
        buffer_size: int = 4096,
    ):
        self.port = port
        self.baudrate = baudrate
        self.buffer_size = buffer_size
        self._codec = COBSCodec()
        self._buffer = bytearray()
        self._serial: Optional[object] = None

    async def connect(self) -> None:
        """Open serial port (requires pyserial)."""
        try:
            import serial
        except ImportError:
            raise ImportError("pyserial required: pip install pyserial")

        self._serial = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            timeout=0.01,
        )
        logger.info("Serial connected: %s @ %d", self.port, self.baudrate)

    async def disconnect(self) -> None:
        """Close serial port."""
        if self._serial and hasattr(self._serial, "close"):
            self._serial.close()
            self._serial = None
        self._buffer.clear()
        logger.info("Serial disconnected: %s", self.port)

    def feed(self, data: bytes) -> list[bytes]:
        """
        Feed raw bytes into buffer; return list of complete COBS frames.
        """
        self._buffer.extend(data)
        frames, remainder = self._codec.extract_frames(bytes(self._buffer))
        self._buffer = bytearray(remainder)
        return frames

    async def read_frames(self) -> AsyncIterator[bytes]:
        """
        Async iterator yielding complete COBS-encoded frames from serial.
        """
        if not self._serial:
            raise RuntimeError("Serial not connected")

        buf = bytearray()
        while True:
            if self._serial.in_waiting:
                chunk = self._serial.read(self._serial.in_waiting)
                buf.extend(chunk)
                frames, remainder = self._codec.extract_frames(bytes(buf))
                buf = bytearray(remainder)
                for frame in frames:
                    yield frame
            await asyncio.sleep(0.01)

    def write_frame(self, frame: bytes) -> int:
        """
        Write a COBS-encoded frame to serial.
        Returns number of bytes written.
        """
        if not self._serial:
            raise RuntimeError("Serial not connected")
        return self._serial.write(frame)

    def write_raw(self, data: bytes) -> int:
        """Write raw bytes (for testing)."""
        if not self._serial:
            raise RuntimeError("Serial not connected")
        return self._serial.write(data)
