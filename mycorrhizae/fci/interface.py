"""
FCI Interface - Fungal Computer Interface Signal Types

Defines signal types, readings, and channels for mycelium computing.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4


class FCISignalType(str, Enum):
    """Types of signals from the Fungal Computer Interface."""
    BIOELECTRIC = "bioelectric"     # Electrical potential from mycelium
    IMPEDANCE = "impedance"         # Electrical impedance changes
    CONDUCTIVITY = "conductivity"   # Substrate conductivity
    CHEMICAL = "chemical"           # Chemical gradients (volatile compounds)
    LIGHT = "light"                 # Bioluminescence (some species)
    PRESSURE = "pressure"           # Mechanical pressure from growth
    TEMPERATURE = "temperature"     # Local temperature
    HUMIDITY = "humidity"           # Local humidity
    CO2 = "co2"                     # CO2 levels from respiration
    VOC = "voc"                     # Volatile organic compounds


@dataclass
class FCIReading:
    """A single reading from the FCI."""
    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    signal_type: FCISignalType = FCISignalType.BIOELECTRIC
    channel_id: int = 0
    
    # Raw values
    raw_value: float = 0.0
    raw_unit: str = "mV"
    
    # Normalized values (0-1 scale)
    normalized_value: float = 0.0
    
    # Quality metrics
    quality: float = 1.0           # Signal quality (0-1)
    noise_level: float = 0.0       # Noise floor
    snr: float = 0.0              # Signal-to-noise ratio
    
    # Calibration
    calibrated: bool = False
    calibration_offset: float = 0.0
    calibration_scale: float = 1.0
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def normalize(self, min_val: float, max_val: float) -> float:
        """Normalize the raw value to 0-1 scale."""
        if max_val == min_val:
            return 0.5
        self.normalized_value = (self.raw_value - min_val) / (max_val - min_val)
        self.normalized_value = max(0.0, min(1.0, self.normalized_value))
        return self.normalized_value
    
    def apply_calibration(self) -> float:
        """Apply calibration to raw value."""
        calibrated = (self.raw_value + self.calibration_offset) * self.calibration_scale
        self.calibrated = True
        return calibrated
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "signal_type": self.signal_type.value,
            "channel_id": self.channel_id,
            "raw_value": self.raw_value,
            "raw_unit": self.raw_unit,
            "normalized_value": self.normalized_value,
            "quality": self.quality,
            "noise_level": self.noise_level,
            "snr": self.snr,
            "calibrated": self.calibrated,
            "metadata": self.metadata,
        }


@dataclass
class FCIChannel:
    """An FCI input channel configuration."""
    id: int
    name: str
    signal_type: FCISignalType
    
    # Physical configuration
    pin: Optional[int] = None      # GPIO pin
    adc_channel: Optional[int] = None  # ADC channel
    
    # Value range
    min_value: float = 0.0
    max_value: float = 1000.0
    unit: str = "mV"
    
    # Sampling
    sample_rate_hz: float = 10.0
    averaging_samples: int = 10
    
    # Thresholds
    alert_low: Optional[float] = None
    alert_high: Optional[float] = None
    
    # State
    enabled: bool = True
    last_reading: Optional[FCIReading] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "signal_type": self.signal_type.value,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "unit": self.unit,
            "sample_rate_hz": self.sample_rate_hz,
            "enabled": self.enabled,
            "last_reading": self.last_reading.to_dict() if self.last_reading else None,
        }


class FCIInterface:
    """
    Interface for the Fungal Computer Interface hardware.
    
    Manages channels, readings, and signal normalization for
    bioelectric signals from mycelium networks.
    """
    
    # Standard channel configurations for MycoBrain devices
    STANDARD_CHANNELS = {
        "bioelectric_1": FCIChannel(0, "Bioelectric 1", FCISignalType.BIOELECTRIC, min_value=-500, max_value=500, unit="mV"),
        "bioelectric_2": FCIChannel(1, "Bioelectric 2", FCISignalType.BIOELECTRIC, min_value=-500, max_value=500, unit="mV"),
        "impedance": FCIChannel(2, "Impedance", FCISignalType.IMPEDANCE, min_value=0, max_value=10000, unit="Ohm"),
        "conductivity": FCIChannel(3, "Conductivity", FCISignalType.CONDUCTIVITY, min_value=0, max_value=2000, unit="uS/cm"),
        "temperature": FCIChannel(4, "Temperature", FCISignalType.TEMPERATURE, min_value=-10, max_value=50, unit="C"),
        "humidity": FCIChannel(5, "Humidity", FCISignalType.HUMIDITY, min_value=0, max_value=100, unit="%"),
        "co2": FCIChannel(6, "CO2", FCISignalType.CO2, min_value=0, max_value=5000, unit="ppm"),
        "voc": FCIChannel(7, "VOC", FCISignalType.VOC, min_value=0, max_value=500, unit="ppb"),
    }
    
    def __init__(self, device_serial: str):
        self.device_serial = device_serial
        self.channels: Dict[str, FCIChannel] = {}
        self.readings: List[FCIReading] = []
        self._max_readings = 1000
        
        # Initialize with standard channels
        for name, channel in self.STANDARD_CHANNELS.items():
            self.channels[name] = FCIChannel(
                id=channel.id,
                name=channel.name,
                signal_type=channel.signal_type,
                min_value=channel.min_value,
                max_value=channel.max_value,
                unit=channel.unit,
            )
    
    def add_channel(self, name: str, channel: FCIChannel) -> None:
        """Add a custom channel."""
        self.channels[name] = channel
    
    def get_channel(self, name: str) -> Optional[FCIChannel]:
        """Get a channel by name."""
        return self.channels.get(name)
    
    def record_reading(
        self,
        channel_name: str,
        raw_value: float,
        quality: float = 1.0,
        noise_level: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[FCIReading]:
        """
        Record a reading from a channel.
        
        Returns the reading with normalization applied.
        """
        channel = self.channels.get(channel_name)
        if not channel or not channel.enabled:
            return None
        
        reading = FCIReading(
            signal_type=channel.signal_type,
            channel_id=channel.id,
            raw_value=raw_value,
            raw_unit=channel.unit,
            quality=quality,
            noise_level=noise_level,
            snr=abs(raw_value) / noise_level if noise_level > 0 else 100.0,
            metadata=metadata or {},
        )
        
        # Normalize
        reading.normalize(channel.min_value, channel.max_value)
        
        # Update channel state
        channel.last_reading = reading
        
        # Store reading
        self.readings.append(reading)
        if len(self.readings) > self._max_readings:
            self.readings = self.readings[-self._max_readings:]
        
        return reading
    
    def get_latest_readings(self, count: int = 10) -> List[FCIReading]:
        """Get the latest readings."""
        return self.readings[-count:]
    
    def get_channel_readings(
        self,
        channel_name: str,
        count: int = 100,
    ) -> List[FCIReading]:
        """Get readings for a specific channel."""
        channel = self.channels.get(channel_name)
        if not channel:
            return []
        
        return [r for r in self.readings if r.channel_id == channel.id][-count:]
    
    def get_aggregate_stats(self) -> Dict[str, Any]:
        """Get aggregate statistics for all channels."""
        stats = {}
        
        for name, channel in self.channels.items():
            readings = self.get_channel_readings(name, 100)
            if not readings:
                continue
            
            values = [r.normalized_value for r in readings]
            stats[name] = {
                "count": len(readings),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "latest": values[-1] if values else 0,
                "quality_avg": sum(r.quality for r in readings) / len(readings),
            }
        
        return stats
    
    def to_mycorrhizae_payload(self) -> Dict[str, Any]:
        """Convert current state to Mycorrhizae message payload."""
        return {
            "device_serial": self.device_serial,
            "channels": {name: ch.to_dict() for name, ch in self.channels.items()},
            "stats": self.get_aggregate_stats(),
            "latest_readings": [r.to_dict() for r in self.get_latest_readings()],
        }
