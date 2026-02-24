"""
MDP v1 Framing: COBS Encoding and CRC-16

COBS (Consistent Overhead Byte Stuffing) ensures no zero bytes in output.
CRC-16-CCITT-FALSE for error detection.
Reference: mycobrain/firmware and MAS protocols/MDP_V1_SPEC.md
"""

import struct
from typing import List, Tuple


class CRC16Calculator:
    """CRC16-CCITT-FALSE calculator (polynomial 0x1021, init 0xFFFF)."""

    POLYNOMIAL = 0x1021
    INIT = 0xFFFF

    def calculate(self, data: bytes) -> int:
        """Compute CRC16 over data."""
        crc = self.INIT
        for byte in data:
            crc ^= (byte << 8)
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ self.POLYNOMIAL
                else:
                    crc <<= 1
                crc &= 0xFFFF
        return crc


class COBSCodec:
    """
    COBS (Consistent Overhead Byte Stuffing) encode/decode.

    Frame format: [0x00][COBS-encoded data][0x00]
    Encoded output has no zero bytes except delimiters.
    """

    DELIMITER = 0x00
    MAX_RUN = 0xFF

    def encode(self, data: bytes) -> bytes:
        """
        Encode data with COBS. Appends 0x00 frame delimiter only.
        Matches MAS and MycoBrain firmware format.
        """
        if not data:
            return bytes([0x01, self.DELIMITER])

        output = bytearray()
        output.append(0x00)  # Placeholder for first code byte
        code_index = 0
        code = 0x01

        for byte in data:
            if byte == self.DELIMITER:
                output[code_index] = code
                code_index = len(output)
                output.append(0x00)
                code = 0x01
            else:
                output.append(byte)
                code += 1
                if code == self.MAX_RUN:
                    output[code_index] = code
                    code_index = len(output)
                    output.append(0x00)
                    code = 0x01

        output[code_index] = code
        output.append(self.DELIMITER)
        return bytes(output)

    def decode(self, data: bytes) -> bytes:
        """
        Decode COBS-encoded data. Expects trailing 0x00 delimiter.
        Raises ValueError if invalid.
        """
        if len(data) < 2:
            raise ValueError("COBS data too short")

        if data[-1] != self.DELIMITER:
            raise ValueError("COBS frame delimiter missing")

        data = data[:-1]  # Strip trailing delimiter
        output = bytearray()
        i = 0

        while i < len(data):
            code = data[i]
            i += 1

            if code == self.DELIMITER:
                raise ValueError("Invalid COBS code byte: 0x00")

            for _ in range(code - 1):
                if i >= len(data):
                    raise ValueError("COBS data truncated")
                output.append(data[i])
                i += 1

            if code < self.MAX_RUN and i < len(data):
                output.append(self.DELIMITER)

        return bytes(output)

    def extract_frames(self, buffer: bytes) -> Tuple[List[bytes], bytes]:
        """
        Extract complete COBS frames from buffer. Returns (frames, remainder).
        Frames end with 0x00 delimiter (no leading delimiter in stream).
        """
        frames: list[bytes] = []
        remainder = bytearray()
        start = 0

        for i in range(len(buffer)):
            if buffer[i] != self.DELIMITER:
                continue
            # Found trailing delimiter - [start:i+1] is one frame
            frame = bytes(buffer[start : i + 1])
            if len(frame) >= 2:
                try:
                    decoded = self.decode(frame)
                    frames.append(decoded)
                except ValueError:
                    pass  # Invalid frame, skip
            start = i + 1

        if start < len(buffer):
            remainder.extend(buffer[start:])

        return (frames, bytes(remainder))
