"""
HPL Device Interface Modules

Provides abstract and concrete device interfaces for FCI hardware.
Enables HPL programs to interact with physical mycelium sensing devices.

Supported devices:
- Mushroom1: Mycosoft's flagship environmental monitor
- MycoBrain: ESP32-based bioelectric sensing peripheral
- SporeBase: Network gateway for distributed sensing
- MycoPetri: Petri dish simulation interface

Example HPL usage:
    substrate MycoBrain {
        device = connect("MycoBrain", "192.168.1.100")
        sense(device.bioelectric) -> signalData
        match(signalData, GrowthSignal) -> isGrowing
    }

(c) 2026 Mycosoft Labs
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from uuid import UUID, uuid4
import asyncio
import json
import os

try:
    import httpx
    HTTPX_AVAILABLE = True
except Exception:
    HTTPX_AVAILABLE = False

from .signal_patterns import Signal, WaveformType


# ============================================================================
# DEVICE TYPES
# ============================================================================

class DeviceType(str, Enum):
    """Types of FCI devices."""
    MUSHROOM1 = "mushroom1"       # Environmental monitor
    MYCOBRAIN = "mycobrain"       # Bioelectric sensing
    SPOREBASE = "sporebase"       # Network gateway
    MYCOPETRI = "mycopetri"       # Petri dish simulation
    GENERIC_FCI = "generic_fci"   # Generic FCI-compatible device
    SIMULATOR = "simulator"       # Software simulator


class DeviceStatus(str, Enum):
    """Device connection status."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    CALIBRATING = "calibrating"
    STREAMING = "streaming"


class ChannelType(str, Enum):
    """Types of sensor channels."""
    BIOELECTRIC = "bioelectric"     # Electrical potential
    IMPEDANCE = "impedance"         # Impedance measurement
    TEMPERATURE = "temperature"     # Temperature
    HUMIDITY = "humidity"           # Relative humidity
    PRESSURE = "pressure"           # Barometric pressure
    CO2 = "co2"                     # CO2 concentration
    VOC = "voc"                     # Volatile organic compounds
    LIGHT = "light"                 # Light level
    MOISTURE = "moisture"           # Substrate moisture
    PH = "ph"                       # pH level
    CONDUCTIVITY = "conductivity"   # Electrical conductivity


# ============================================================================
# CHANNEL DEFINITION
# ============================================================================

@dataclass
class Channel:
    """A sensor channel on a device."""
    
    id: str
    name: str
    channel_type: ChannelType
    
    # Physical properties
    unit: str = ""
    min_value: float = 0.0
    max_value: float = 1.0
    resolution: float = 0.001
    sample_rate_hz: float = 10.0
    
    # Calibration
    offset: float = 0.0
    scale: float = 1.0
    calibrated: bool = False
    
    # Current state
    last_value: Optional[float] = None
    last_timestamp: Optional[datetime] = None
    
    def apply_calibration(self, raw_value: float) -> float:
        """Apply calibration to raw value."""
        return (raw_value + self.offset) * self.scale
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.channel_type.value,
            "unit": self.unit,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "sample_rate_hz": self.sample_rate_hz,
            "calibrated": self.calibrated,
            "last_value": self.last_value,
        }


# ============================================================================
# ABSTRACT DEVICE INTERFACE
# ============================================================================

class DeviceInterface(ABC):
    """
    Abstract base class for all FCI device interfaces.
    
    Provides the contract that all device drivers must implement.
    """
    
    def __init__(
        self,
        device_id: str,
        device_type: DeviceType,
        name: str = "",
    ):
        self.device_id = device_id
        self.device_type = device_type
        self.name = name or f"{device_type.value}_{device_id[:8]}"
        self.status = DeviceStatus.DISCONNECTED
        self.channels: Dict[str, Channel] = {}
        self.metadata: Dict[str, Any] = {}
        
        # Connection info
        self.host: Optional[str] = None
        self.port: Optional[int] = None
        self.serial_port: Optional[str] = None
        
        # Callbacks
        self._on_data: Optional[Callable[[str, float, datetime], None]] = None
        self._on_status: Optional[Callable[[DeviceStatus], None]] = None
        self._on_error: Optional[Callable[[Exception], None]] = None
    
    @abstractmethod
    async def connect(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        serial_port: Optional[str] = None,
    ) -> bool:
        """Connect to the device."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from the device."""
        pass
    
    @abstractmethod
    async def read_channel(self, channel_id: str) -> Optional[float]:
        """Read a single value from a channel."""
        pass
    
    @abstractmethod
    async def read_all_channels(self) -> Dict[str, float]:
        """Read all channels."""
        pass
    
    @abstractmethod
    async def calibrate(self, channel_id: Optional[str] = None) -> bool:
        """Calibrate channel(s)."""
        pass
    
    @abstractmethod
    async def start_streaming(self, channels: Optional[List[str]] = None) -> bool:
        """Start continuous data streaming."""
        pass
    
    @abstractmethod
    async def stop_streaming(self) -> bool:
        """Stop data streaming."""
        pass
    
    def on_data(self, callback: Callable[[str, float, datetime], None]) -> None:
        """Register data callback."""
        self._on_data = callback
    
    def on_status_change(self, callback: Callable[[DeviceStatus], None]) -> None:
        """Register status change callback."""
        self._on_status = callback
    
    def on_error(self, callback: Callable[[Exception], None]) -> None:
        """Register error callback."""
        self._on_error = callback
    
    def _notify_data(self, channel_id: str, value: float, timestamp: datetime) -> None:
        """Notify data callback."""
        if self._on_data:
            self._on_data(channel_id, value, timestamp)
    
    def _notify_status(self, status: DeviceStatus) -> None:
        """Notify status change."""
        self.status = status
        if self._on_status:
            self._on_status(status)
    
    def _notify_error(self, error: Exception) -> None:
        """Notify error."""
        if self._on_error:
            self._on_error(error)
    
    def get_channel(self, channel_id: str) -> Optional[Channel]:
        """Get a channel by ID."""
        return self.channels.get(channel_id)
    
    def list_channels(self) -> List[Channel]:
        """List all channels."""
        return list(self.channels.values())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "device_id": self.device_id,
            "device_type": self.device_type.value,
            "name": self.name,
            "status": self.status.value,
            "channels": {k: v.to_dict() for k, v in self.channels.items()},
            "metadata": self.metadata,
        }


# ============================================================================
# MYCOBRAIN DEVICE
# ============================================================================

class MycoBrainDevice(DeviceInterface):
    """
    MycoBrain FCI Device Interface
    
    ESP32-based bioelectric sensing peripheral with:
    - 2 differential bioelectric channels (ADS1115)
    - Environmental sensors (BME688)
    - Impedance measurement
    - Bi-directional stimulation capability
    """
    
    # MycoBrain channel definitions
    DEFAULT_CHANNELS = [
        Channel("bio_1", "Bioelectric 1", ChannelType.BIOELECTRIC, "uV", -500, 500, 0.125, 128),
        Channel("bio_2", "Bioelectric 2", ChannelType.BIOELECTRIC, "uV", -500, 500, 0.125, 128),
        Channel("impedance", "Impedance", ChannelType.IMPEDANCE, "Ohm", 0, 1000000, 10, 1),
        Channel("temp", "Temperature", ChannelType.TEMPERATURE, "C", -40, 85, 0.01, 1),
        Channel("humidity", "Humidity", ChannelType.HUMIDITY, "%RH", 0, 100, 0.1, 1),
        Channel("pressure", "Pressure", ChannelType.PRESSURE, "hPa", 300, 1100, 0.1, 1),
        Channel("voc", "VOC Index", ChannelType.VOC, "idx", 0, 500, 1, 1),
    ]
    
    def __init__(self, device_id: Optional[str] = None, name: str = ""):
        super().__init__(
            device_id=device_id or str(uuid4()),
            device_type=DeviceType.MYCOBRAIN,
            name=name or "MycoBrain",
        )
        
        # Initialize default channels
        for ch in self.DEFAULT_CHANNELS:
            self.channels[ch.id] = Channel(
                id=ch.id,
                name=ch.name,
                channel_type=ch.channel_type,
                unit=ch.unit,
                min_value=ch.min_value,
                max_value=ch.max_value,
                resolution=ch.resolution,
                sample_rate_hz=ch.sample_rate_hz,
            )
        
        # MycoBrain-specific state
        self._websocket = None
        self._streaming = False
        self._signal_buffer: Dict[str, List[Tuple[float, datetime]]] = {
            "bio_1": [],
            "bio_2": [],
        }
        self._buffer_size = 256
        
        # Firmware info
        self.firmware_version: Optional[str] = None
        self.mac_address: Optional[str] = None
        self._service_url: Optional[str] = None
        self._remote_device_id: Optional[str] = None

    def _resolve_service_url(self, host: Optional[str], port: Optional[int]) -> Optional[str]:
        if host:
            if host.startswith("http://") or host.startswith("https://"):
                return host.rstrip("/")
            return f"http://{host}:{port or 8003}"
        env_url = os.getenv("MYCOBRAIN_SERVICE_URL")
        if env_url:
            return env_url.rstrip("/")
        return None
    
    async def connect(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        serial_port: Optional[str] = None,
    ) -> bool:
        """Connect to MycoBrain device."""
        self._notify_status(DeviceStatus.CONNECTING)
        
        try:
            if not HTTPX_AVAILABLE:
                raise RuntimeError("httpx not available - cannot connect to MycoBrain service")

            self._service_url = self._resolve_service_url(host, port)
            if not self._service_url:
                raise ValueError("MYCOBRAIN_SERVICE_URL not configured and no host provided")

            async with httpx.AsyncClient(timeout=10.0) as client:
                health = await client.get(f"{self._service_url}/health")
                if health.status_code != 200:
                    raise RuntimeError(f"MycoBrain service unhealthy: {health.status_code}")

                if serial_port:
                    response = await client.post(
                        f"{self._service_url}/devices/connect/{serial_port}"
                    )
                    response.raise_for_status()
                    payload = response.json()
                    self._remote_device_id = payload.get("device_id")
                else:
                    devices = await client.get(f"{self._service_url}/devices")
                    devices.raise_for_status()
                    payload = devices.json()
                    device_list = payload.get("devices", [])
                    if not device_list:
                        raise RuntimeError("No connected MycoBrain devices found")
                    self._remote_device_id = device_list[0].get("device_id")

            self.host = host
            self.port = port or 8003
            self.serial_port = serial_port
            self._notify_status(DeviceStatus.CONNECTED)
            return True
            
        except Exception as e:
            self._notify_status(DeviceStatus.ERROR)
            self._notify_error(e)
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from MycoBrain device."""
        try:
            await self.stop_streaming()
            
            if self._websocket:
                # await self._websocket.close()
                self._websocket = None
            
            self._notify_status(DeviceStatus.DISCONNECTED)
            return True
            
        except Exception as e:
            self._notify_error(e)
            return False
    
    async def read_channel(self, channel_id: str) -> Optional[float]:
        """Read a single channel value."""
        channel = self.channels.get(channel_id)
        if not channel:
            return None

        if not HTTPX_AVAILABLE or not self._service_url or not self._remote_device_id:
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self._service_url}/devices/{self._remote_device_id}/telemetry"
                )
                response.raise_for_status()
                payload = response.json().get("telemetry", {})
                bme = payload.get("bme1") or payload.get("bme2") or {}
                value_map = {
                    "temp": bme.get("temperature"),
                    "humidity": bme.get("humidity"),
                    "pressure": bme.get("pressure"),
                    "voc": bme.get("iaq"),
                }
                if channel_id in value_map and value_map[channel_id] is not None:
                    value = float(value_map[channel_id])
                    channel.last_value = value
                    channel.last_timestamp = datetime.now(timezone.utc)
                    return value
        except Exception:
            return None

        if channel_id in self._signal_buffer and self._signal_buffer[channel_id]:
            return self._signal_buffer[channel_id][-1][0]

        return None
    
    async def read_all_channels(self) -> Dict[str, float]:
        """Read all channels."""
        values = {}
        
        for channel_id in self.channels:
            value = await self.read_channel(channel_id)
            if value is not None:
                values[channel_id] = value
        
        return values
    
    async def calibrate(self, channel_id: Optional[str] = None) -> bool:
        """Calibrate bioelectric channels."""
        self._notify_status(DeviceStatus.CALIBRATING)
        
        try:
            if not HTTPX_AVAILABLE or not self._service_url or not self._remote_device_id:
                raise RuntimeError("MycoBrain service not configured for calibration")

            self._notify_status(DeviceStatus.CONNECTED)
            return False
            
        except Exception as e:
            self._notify_error(e)
            self._notify_status(DeviceStatus.ERROR)
            return False
    
    async def start_streaming(self, channels: Optional[List[str]] = None) -> bool:
        """Start streaming bioelectric data."""
        try:
            if not HTTPX_AVAILABLE or not self._service_url or not self._remote_device_id:
                return False
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self._service_url}/devices/{self._remote_device_id}/command",
                    json={"raw_command": "live on"},
                )
                response.raise_for_status()
            self._streaming = True
            self._notify_status(DeviceStatus.STREAMING)
            return True
            
        except Exception as e:
            self._notify_error(e)
            return False
    
    async def stop_streaming(self) -> bool:
        """Stop data streaming."""
        try:
            if not HTTPX_AVAILABLE or not self._service_url or not self._remote_device_id:
                return False
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self._service_url}/devices/{self._remote_device_id}/command",
                    json={"raw_command": "live off"},
                )
                response.raise_for_status()
            self._streaming = False
            self._notify_status(DeviceStatus.CONNECTED)
            return True
            
        except Exception as e:
            self._notify_error(e)
            return False
    
    def get_signal(self, channel_id: str = "bio_1") -> Signal:
        """
        Get buffered signal data as an HPL Signal object.
        
        This is the bridge between device data and HPL pattern matching.
        """
        buffer = self._signal_buffer.get(channel_id, [])
        
        if not buffer:
            return Signal(sample_rate_hz=128.0, channel_id=channel_id, device_id=self.device_id)
        
        samples = [v for v, t in buffer]
        
        signal = Signal(
            samples=samples,
            sample_rate_hz=self.channels[channel_id].sample_rate_hz if channel_id in self.channels else 128.0,
            timestamp=buffer[-1][1] if buffer else datetime.now(timezone.utc),
            channel_id=channel_id,
            device_id=self.device_id,
            probe_type="mycobrain",
        )
        
        return signal
    
    def add_sample(self, channel_id: str, value: float, timestamp: Optional[datetime] = None) -> None:
        """Add a sample to the buffer."""
        if channel_id not in self._signal_buffer:
            self._signal_buffer[channel_id] = []
        
        ts = timestamp or datetime.now(timezone.utc)
        self._signal_buffer[channel_id].append((value, ts))
        
        # Trim buffer
        if len(self._signal_buffer[channel_id]) > self._buffer_size:
            self._signal_buffer[channel_id] = self._signal_buffer[channel_id][-self._buffer_size:]
        
        # Update channel last value
        if channel_id in self.channels:
            self.channels[channel_id].last_value = value
            self.channels[channel_id].last_timestamp = ts
        
        # Notify
        self._notify_data(channel_id, value, ts)
    
    async def send_stimulus(
        self,
        waveform: str = "pulse",
        amplitude_uv: float = 100.0,
        frequency_hz: float = 1.0,
        duration_ms: int = 1000,
    ) -> bool:
        """
        Send electrical stimulus to mycelium (bi-directional interface).
        
        WARNING: Only use with proper safety protocols.
        """
        try:
            command = {
                "type": "stimulus",
                "waveform": waveform,
                "amplitude_uv": amplitude_uv,
                "frequency_hz": frequency_hz,
                "duration_ms": duration_ms,
            }

            if not HTTPX_AVAILABLE or not self._service_url or not self._remote_device_id:
                return False

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self._service_url}/devices/{self._remote_device_id}/command",
                    json={"raw_command": json.dumps(command)},
                )
                response.raise_for_status()
                return True
            
        except Exception as e:
            self._notify_error(e)
            return False


# ============================================================================
# MUSHROOM1 DEVICE
# ============================================================================

class Mushroom1Device(DeviceInterface):
    """
    Mushroom1 Environmental Monitor Interface
    
    Mycosoft's flagship environmental monitoring device with:
    - Temperature and humidity sensors
    - Air quality sensors (CO2, VOC)
    - Light level sensing
    - Substrate moisture monitoring
    """
    
    DEFAULT_CHANNELS = [
        Channel("temp", "Temperature", ChannelType.TEMPERATURE, "C", -40, 85, 0.01, 1),
        Channel("humidity", "Humidity", ChannelType.HUMIDITY, "%RH", 0, 100, 0.1, 1),
        Channel("co2", "CO2", ChannelType.CO2, "ppm", 400, 5000, 1, 0.5),
        Channel("voc", "VOC", ChannelType.VOC, "ppb", 0, 1000, 1, 0.5),
        Channel("light", "Light Level", ChannelType.LIGHT, "lux", 0, 100000, 1, 1),
        Channel("moisture", "Substrate Moisture", ChannelType.MOISTURE, "%", 0, 100, 0.1, 0.1),
    ]
    
    def __init__(self, device_id: Optional[str] = None, name: str = ""):
        super().__init__(
            device_id=device_id or str(uuid4()),
            device_type=DeviceType.MUSHROOM1,
            name=name or "Mushroom1",
        )
        
        for ch in self.DEFAULT_CHANNELS:
            self.channels[ch.id] = Channel(
                id=ch.id, name=ch.name, channel_type=ch.channel_type,
                unit=ch.unit, min_value=ch.min_value, max_value=ch.max_value,
                resolution=ch.resolution, sample_rate_hz=ch.sample_rate_hz,
            )
        self._service_url: Optional[str] = None
    
    def _resolve_service_url(self, host: Optional[str], port: Optional[int]) -> Optional[str]:
        if host:
            if host.startswith("http://") or host.startswith("https://"):
                return host.rstrip("/")
            return f"http://{host}:{port or 8003}"
        env_url = os.getenv("MUSHROOM1_DEVICE_URL")
        if env_url:
            return env_url.rstrip("/")
        return None
    
    async def _fetch_telemetry(self) -> Optional[Dict[str, Any]]:
        if not HTTPX_AVAILABLE or not self._service_url:
            return None
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self._service_url}/telemetry")
                response.raise_for_status()
                return response.json()
        except Exception:
            return None
    
    async def connect(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        serial_port: Optional[str] = None,
    ) -> bool:
        """Connect to Mushroom1 via MQTT or REST API."""
        self._notify_status(DeviceStatus.CONNECTING)
        
        try:
            if not HTTPX_AVAILABLE:
                raise RuntimeError("httpx not available - cannot connect to Mushroom1 service")
            self._service_url = self._resolve_service_url(host, port)
            if not self._service_url:
                raise ValueError("MUSHROOM1_DEVICE_URL not configured and no host provided")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self._service_url}/health")
                if response.status_code != 200:
                    raise RuntimeError(f"Mushroom1 service unhealthy: {response.status_code}")
            self.host = host
            self.port = port or 8003
            self._notify_status(DeviceStatus.CONNECTED)
            return True
            
        except Exception as e:
            self._notify_status(DeviceStatus.ERROR)
            self._notify_error(e)
            return False
    
    async def disconnect(self) -> bool:
        self._notify_status(DeviceStatus.DISCONNECTED)
        return True
    
    async def read_channel(self, channel_id: str) -> Optional[float]:
        channel = self.channels.get(channel_id)
        if channel:
            telemetry = await self._fetch_telemetry()
            if telemetry and channel_id in telemetry:
                try:
                    value = float(telemetry[channel_id])
                    channel.last_value = value
                    channel.last_timestamp = datetime.now(timezone.utc)
                    return value
                except Exception:
                    return None
            return channel.last_value
        return None
    
    async def read_all_channels(self) -> Dict[str, float]:
        telemetry = await self._fetch_telemetry()
        if telemetry:
            values = {}
            for channel_id in self.channels:
                if channel_id in telemetry and telemetry[channel_id] is not None:
                    try:
                        value = float(telemetry[channel_id])
                        self.channels[channel_id].last_value = value
                        self.channels[channel_id].last_timestamp = datetime.now(timezone.utc)
                        values[channel_id] = value
                    except Exception:
                        continue
            return values
        return {k: v.last_value for k, v in self.channels.items() if v.last_value is not None}
    
    async def calibrate(self, channel_id: Optional[str] = None) -> bool:
        return True
    
    async def start_streaming(self, channels: Optional[List[str]] = None) -> bool:
        self._notify_status(DeviceStatus.STREAMING)
        return True
    
    async def stop_streaming(self) -> bool:
        self._notify_status(DeviceStatus.CONNECTED)
        return True


# ============================================================================
# SPOREBASE GATEWAY
# ============================================================================

class SporeBaseDevice(DeviceInterface):
    """
    SporeBase Network Gateway Interface
    
    Central hub for distributed FCI sensor network:
    - Aggregates data from multiple MycoBrain/Mushroom1 devices
    - LoRa WAN connectivity for long-range sensing
    - Edge processing for pattern detection
    """
    
    def __init__(self, device_id: Optional[str] = None, name: str = ""):
        super().__init__(
            device_id=device_id or str(uuid4()),
            device_type=DeviceType.SPOREBASE,
            name=name or "SporeBase",
        )
        
        # Connected devices
        self.connected_devices: Dict[str, DeviceInterface] = {}
        self._service_url: Optional[str] = None

    def _resolve_service_url(self, host: Optional[str], port: Optional[int]) -> Optional[str]:
        if host:
            if host.startswith("http://") or host.startswith("https://"):
                return host.rstrip("/")
            return f"http://{host}:{port or 8003}"
        env_url = os.getenv("SPOREBASE_GATEWAY_URL")
        if env_url:
            return env_url.rstrip("/")
        return None
    
    def add_device(self, device: DeviceInterface) -> None:
        """Add a device to the gateway."""
        self.connected_devices[device.device_id] = device
    
    def remove_device(self, device_id: str) -> None:
        """Remove a device from the gateway."""
        if device_id in self.connected_devices:
            del self.connected_devices[device_id]
    
    async def connect(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        serial_port: Optional[str] = None,
    ) -> bool:
        self._notify_status(DeviceStatus.CONNECTING)
        try:
            if not HTTPX_AVAILABLE:
                raise RuntimeError("httpx not available - cannot connect to SporeBase gateway")
            self._service_url = self._resolve_service_url(host, port)
            if not self._service_url:
                raise ValueError("SPOREBASE_GATEWAY_URL not configured and no host provided")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self._service_url}/health")
                if response.status_code != 200:
                    raise RuntimeError(f"SporeBase gateway unhealthy: {response.status_code}")
            self.host = host
            self.port = port or 8003
            self._notify_status(DeviceStatus.CONNECTED)
            return True
        except Exception as exc:
            self._notify_status(DeviceStatus.ERROR)
            self._notify_error(exc)
            return False
    
    async def disconnect(self) -> bool:
        for device in self.connected_devices.values():
            await device.disconnect()
        
        self._notify_status(DeviceStatus.DISCONNECTED)
        return True
    
    async def read_channel(self, channel_id: str) -> Optional[float]:
        return None  # Gateway aggregates, not reads directly
    
    async def read_all_channels(self) -> Dict[str, float]:
        return {}
    
    async def calibrate(self, channel_id: Optional[str] = None) -> bool:
        return True
    
    async def start_streaming(self, channels: Optional[List[str]] = None) -> bool:
        for device in self.connected_devices.values():
            await device.start_streaming(channels)
        self._notify_status(DeviceStatus.STREAMING)
        return True
    
    async def stop_streaming(self) -> bool:
        for device in self.connected_devices.values():
            await device.stop_streaming()
        self._notify_status(DeviceStatus.CONNECTED)
        return True


# ============================================================================
# DEVICE MANAGER (HPL built-in)
# ============================================================================

class DeviceManager:
    """
    Global device manager for HPL programs.
    
    Provides the connect() function for HPL:
        device = connect("MycoBrain", "192.168.1.100")
    """
    
    def __init__(self):
        self.devices: Dict[str, DeviceInterface] = {}
        self._device_factories: Dict[str, type] = {
            "mycobrain": MycoBrainDevice,
            "mushroom1": Mushroom1Device,
            "sporebase": SporeBaseDevice,
        }
    
    async def connect(
        self,
        device_type: str,
        host: Optional[str] = None,
        port: Optional[int] = None,
        serial_port: Optional[str] = None,
        device_id: Optional[str] = None,
    ) -> Optional[DeviceInterface]:
        """
        HPL connect() function - establish connection to a device.
        
        Usage in HPL:
            device = connect("MycoBrain", "192.168.1.100")
        """
        device_type_lower = device_type.lower()
        
        factory = self._device_factories.get(device_type_lower)
        if not factory:
            return None
        
        device = factory(device_id=device_id)
        
        success = await device.connect(host=host, port=port, serial_port=serial_port)
        
        if success:
            self.devices[device.device_id] = device
            return device
        
        return None
    
    async def disconnect(self, device_id: str) -> bool:
        """Disconnect a device."""
        device = self.devices.get(device_id)
        if device:
            success = await device.disconnect()
            if success:
                del self.devices[device_id]
            return success
        return False
    
    def get_device(self, device_id: str) -> Optional[DeviceInterface]:
        """Get a device by ID."""
        return self.devices.get(device_id)
    
    def list_devices(self) -> List[Dict[str, Any]]:
        """List all connected devices."""
        return [d.to_dict() for d in self.devices.values()]
    
    def register_device_type(self, name: str, factory: type) -> None:
        """Register a custom device type."""
        self._device_factories[name.lower()] = factory


# Global device manager instance
_global_device_manager = DeviceManager()


# HPL built-in functions
async def connect(
    device_type: str,
    host: Optional[str] = None,
    port: Optional[int] = None,
    serial_port: Optional[str] = None,
) -> Optional[DeviceInterface]:
    """
    HPL connect() function.
    
    Usage:
        device = connect("MycoBrain", "192.168.1.100")
    """
    return await _global_device_manager.connect(device_type, host, port, serial_port)


def get_device_manager() -> DeviceManager:
    """Get the global device manager."""
    return _global_device_manager
