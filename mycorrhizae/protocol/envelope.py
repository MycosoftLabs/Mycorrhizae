"""
Mycorrhizae Protocol - Envelope Format and Message Handling

Implements the core message envelope format for the Mycorrhizae Protocol.
This is the foundational data structure for all FCI communication.

Version: 1.0.0

(c) 2026 Mycosoft Labs
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID, uuid4
import hashlib
import json

# Optional cryptography for message signing
try:
    from nacl.signing import SigningKey, VerifyKey
    from nacl.encoding import Base64Encoder
    HAS_NACL = True
except ImportError:
    HAS_NACL = False


# ============================================================================
# PROTOCOL CONSTANTS
# ============================================================================

PROTOCOL_VERSION = "1.0.0"
DEFAULT_TTL_SECONDS = 3600
MAX_MESSAGE_SIZE_BYTES = 1024 * 1024  # 1 MB

# Frequency bands (Hz) - based on GFST
FREQ_ULTRA_LOW = (0.01, 0.1)   # Seismic, slow metabolic
FREQ_LOW = (0.1, 1.0)          # Growth, slow activity
FREQ_MID = (1.0, 10.0)         # Active processes
FREQ_HIGH = (10.0, 50.0)       # Fast activity, stress

# Amplitude ranges (µV)
AMP_BASELINE = (0.0, 0.3)
AMP_GROWTH = (0.5, 2.0)
AMP_STRESS = (1.0, 10.0)
AMP_SPIKE = (2.0, 100.0)


# ============================================================================
# ENUMS
# ============================================================================

class SourceType(str, Enum):
    """Types of message sources."""
    FCI = "fci"                 # Fungal Computer Interface device
    ENVIRONMENT = "environment" # Environmental sensor
    GATEWAY = "gateway"         # Network gateway
    SIMULATOR = "simulator"     # Software simulator
    HPL = "hpl"                 # HPL program


class MessageType(str, Enum):
    """Types of Mycorrhizae messages."""
    FCI_TELEMETRY = "fci_telemetry"
    PATTERN_EVENT = "pattern_event"
    ENVIRONMENT_DATA = "environment_data"
    STIMULUS_COMMAND = "stimulus_command"
    STIMULUS_RESPONSE = "stimulus_response"
    CALIBRATION = "calibration"
    DEVICE_STATUS = "device_status"
    HEARTBEAT = "heartbeat"
    ALERT = "alert"
    HPL_RESULT = "hpl_result"


class ProbeType(str, Enum):
    """FCI probe types."""
    TYPE_A = "type_a"  # Copper-steel with agar
    TYPE_B = "type_b"  # Silver/AgCl reference
    TYPE_C = "type_c"  # Platinum-iridium
    TYPE_D = "type_d"  # Carbon fiber
    CUSTOM = "custom"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class GeoLocation:
    """Geographic location."""
    latitude: float
    longitude: float
    altitude_m: Optional[float] = None
    accuracy_m: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        d = {"latitude": self.latitude, "longitude": self.longitude}
        if self.altitude_m is not None:
            d["altitude_m"] = self.altitude_m
        if self.accuracy_m is not None:
            d["accuracy_m"] = self.accuracy_m
        return d
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GeoLocation":
        return cls(
            latitude=data["latitude"],
            longitude=data["longitude"],
            altitude_m=data.get("altitude_m"),
            accuracy_m=data.get("accuracy_m"),
        )


@dataclass
class Source:
    """Message source information."""
    type: SourceType
    device_id: str
    device_serial: Optional[str] = None
    firmware_version: Optional[str] = None
    probe_type: Optional[ProbeType] = None
    location: Optional[GeoLocation] = None
    
    def to_dict(self) -> Dict[str, Any]:
        d = {
            "type": self.type.value,
            "id": self.device_id,
        }
        if self.device_serial:
            d["device_serial"] = self.device_serial
        if self.firmware_version:
            d["firmware"] = self.firmware_version
        if self.probe_type:
            d["probe_type"] = self.probe_type.value
        if self.location:
            d["location"] = self.location.to_dict()
        return d
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Source":
        return cls(
            type=SourceType(data["type"]),
            device_id=data["id"],
            device_serial=data.get("device_serial"),
            firmware_version=data.get("firmware"),
            probe_type=ProbeType(data["probe_type"]) if data.get("probe_type") else None,
            location=GeoLocation.from_dict(data["location"]) if data.get("location") else None,
        )


@dataclass
class Signature:
    """Cryptographic signature for message authentication."""
    algorithm: str = "ed25519"
    public_key: Optional[str] = None
    signature: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "public_key": self.public_key,
            "signature": self.signature,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Signature":
        return cls(
            algorithm=data.get("algorithm", "ed25519"),
            public_key=data.get("public_key"),
            signature=data.get("signature"),
        )


# ============================================================================
# PAYLOAD TYPES
# ============================================================================

@dataclass
class BioelectricChannelData:
    """Bioelectric signal data for a single channel."""
    id: str
    amplitude_uv: float = 0.0
    rms_uv: float = 0.0
    mean_uv: float = 0.0
    std_uv: float = 0.0
    dominant_freq_hz: float = 0.0
    spectral_centroid_hz: float = 0.0
    total_power: float = 0.0
    band_powers: Dict[str, float] = field(default_factory=lambda: {
        "ultra_low": 0.0,
        "low": 0.0,
        "mid": 0.0,
        "high": 0.0,
    })
    snr_db: float = 0.0
    quality_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "amplitude_uv": self.amplitude_uv,
            "rms_uv": self.rms_uv,
            "mean_uv": self.mean_uv,
            "std_uv": self.std_uv,
            "dominant_freq_hz": self.dominant_freq_hz,
            "spectral_centroid_hz": self.spectral_centroid_hz,
            "total_power": self.total_power,
            "band_powers": self.band_powers,
            "snr_db": self.snr_db,
            "quality_score": self.quality_score,
        }


@dataclass
class PatternData:
    """Detected pattern information."""
    detected: str = "baseline"
    confidence: float = 0.0
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    spike_count: int = 0
    spike_rate_hz: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "detected": self.detected,
            "confidence": self.confidence,
            "alternatives": self.alternatives,
            "spike_count": self.spike_count,
            "spike_rate_hz": self.spike_rate_hz,
        }


@dataclass
class EnvironmentData:
    """Environmental sensor data."""
    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    pressure_hpa: Optional[float] = None
    voc_index: Optional[int] = None
    co2_ppm: Optional[int] = None
    light_lux: Optional[float] = None
    moisture_pct: Optional[float] = None
    ph: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        d = {}
        if self.temperature_c is not None:
            d["temperature_c"] = self.temperature_c
        if self.humidity_pct is not None:
            d["humidity_pct"] = self.humidity_pct
        if self.pressure_hpa is not None:
            d["pressure_hpa"] = self.pressure_hpa
        if self.voc_index is not None:
            d["voc_index"] = self.voc_index
        if self.co2_ppm is not None:
            d["co2_ppm"] = self.co2_ppm
        if self.light_lux is not None:
            d["light_lux"] = self.light_lux
        if self.moisture_pct is not None:
            d["moisture_pct"] = self.moisture_pct
        if self.ph is not None:
            d["ph"] = self.ph
        return d


@dataclass
class FCITelemetryPayload:
    """Payload for FCI telemetry messages."""
    bioelectric_channels: List[BioelectricChannelData] = field(default_factory=list)
    pattern: PatternData = field(default_factory=PatternData)
    environment: EnvironmentData = field(default_factory=EnvironmentData)
    cross_correlation: Optional[Dict[str, Any]] = None
    stimulus_active: bool = False
    device_status: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        d = {
            "bioelectric": {
                "channels": [ch.to_dict() for ch in self.bioelectric_channels],
            },
            "pattern": self.pattern.to_dict(),
            "environment": self.environment.to_dict(),
            "stimulus": {"active": self.stimulus_active},
            "device_status": self.device_status,
        }
        if self.cross_correlation:
            d["bioelectric"]["cross_correlation"] = self.cross_correlation
        return d


@dataclass
class PatternEventPayload:
    """Payload for pattern event messages."""
    event_type: str = "pattern_detected"
    pattern_name: str = ""
    category: str = ""
    confidence: float = 0.0
    start_time: Optional[datetime] = None
    duration_ms: float = 0.0
    features: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    interpretation: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "pattern": {
                "name": self.pattern_name,
                "category": self.category,
                "confidence": self.confidence,
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "duration_ms": self.duration_ms,
                "features": self.features,
            },
            "context": self.context,
            "interpretation": self.interpretation,
        }


@dataclass
class StimulusCommandPayload:
    """Payload for stimulus command messages."""
    command: str = "start_stimulus"
    waveform: str = "pulse"
    amplitude_uv: float = 50.0
    frequency_hz: float = 1.0
    duration_ms: int = 1000
    custom_samples: Optional[List[float]] = None
    max_amplitude_uv: float = 100.0
    max_duration_ms: int = 60000
    require_confirmation: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        d = {
            "command": self.command,
            "parameters": {
                "waveform": self.waveform,
                "amplitude_uv": self.amplitude_uv,
                "frequency_hz": self.frequency_hz,
                "duration_ms": self.duration_ms,
            },
            "safety": {
                "max_amplitude_uv": self.max_amplitude_uv,
                "max_duration_ms": self.max_duration_ms,
                "require_confirmation": self.require_confirmation,
            },
        }
        if self.custom_samples:
            d["parameters"]["custom_samples"] = self.custom_samples
        return d


# ============================================================================
# ENVELOPE CLASS
# ============================================================================

@dataclass
class MycorrhizaeEnvelope:
    """
    The Mycorrhizae Protocol envelope.
    
    This is the standard wrapper for all messages in the Mycorrhizae Protocol.
    """
    
    # Envelope metadata
    version: str = PROTOCOL_VERSION
    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires: Optional[datetime] = None
    ttl_seconds: int = DEFAULT_TTL_SECONDS
    
    # Routing
    channel: str = ""
    message_type: MessageType = MessageType.FCI_TELEMETRY
    
    # Source
    source: Optional[Source] = None
    
    # Security
    signature: Optional[Signature] = None
    
    # Payload
    payload: Union[Dict[str, Any], FCITelemetryPayload, PatternEventPayload, StimulusCommandPayload] = field(default_factory=dict)
    
    def __post_init__(self):
        """Set defaults after initialization."""
        if self.expires is None:
            self.expires = self.timestamp + timedelta(seconds=self.ttl_seconds)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        d = {
            "version": self.version,
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "expires": self.expires.isoformat() if self.expires else None,
            "ttl_seconds": self.ttl_seconds,
            "channel": self.channel,
            "message_type": self.message_type.value,
        }
        
        if self.source:
            d["source"] = self.source.to_dict()
        
        if self.signature and self.signature.signature:
            d["signature"] = self.signature.to_dict()
        
        if hasattr(self.payload, 'to_dict'):
            d["payload"] = self.payload.to_dict()
        else:
            d["payload"] = self.payload
        
        return d
    
    def to_json(self, indent: Optional[int] = None) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MycorrhizaeEnvelope":
        """Create envelope from dictionary."""
        envelope = cls(
            version=data.get("version", PROTOCOL_VERSION),
            id=UUID(data["id"]) if isinstance(data.get("id"), str) else data.get("id", uuid4()),
            timestamp=datetime.fromisoformat(data["timestamp"]) if isinstance(data.get("timestamp"), str) else data.get("timestamp", datetime.now(timezone.utc)),
            expires=datetime.fromisoformat(data["expires"]) if data.get("expires") else None,
            ttl_seconds=data.get("ttl_seconds", DEFAULT_TTL_SECONDS),
            channel=data.get("channel", ""),
            message_type=MessageType(data["message_type"]) if data.get("message_type") else MessageType.FCI_TELEMETRY,
            source=Source.from_dict(data["source"]) if data.get("source") else None,
            signature=Signature.from_dict(data["signature"]) if data.get("signature") else None,
            payload=data.get("payload", {}),
        )
        return envelope
    
    @classmethod
    def from_json(cls, json_str: str) -> "MycorrhizaeEnvelope":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def is_expired(self) -> bool:
        """Check if message has expired."""
        if self.expires is None:
            return False
        return datetime.now(timezone.utc) > self.expires
    
    def is_valid(self) -> Tuple[bool, List[str]]:
        """
        Validate envelope structure.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not self.version:
            errors.append("Missing version")
        
        if not self.id:
            errors.append("Missing id")
        
        if not self.timestamp:
            errors.append("Missing timestamp")
        
        if not self.channel:
            errors.append("Missing channel")
        
        if not self.source:
            errors.append("Missing source")
        
        if self.is_expired():
            errors.append("Message has expired")
        
        return len(errors) == 0, errors
    
    def sign(self, private_key_bytes: bytes) -> bool:
        """
        Sign the envelope using Ed25519.
        
        Args:
            private_key_bytes: 32-byte Ed25519 private key seed
            
        Returns:
            True if signed successfully
        """
        if not HAS_NACL:
            return False
        
        try:
            signing_key = SigningKey(private_key_bytes)
            verify_key = signing_key.verify_key
            
            # Serialize payload for signing
            payload_json = json.dumps(
                self.payload.to_dict() if hasattr(self.payload, 'to_dict') else self.payload,
                sort_keys=True,
                default=str
            )
            payload_hash = hashlib.sha256(payload_json.encode()).digest()
            
            # Sign
            signed = signing_key.sign(payload_hash, encoder=Base64Encoder)
            
            self.signature = Signature(
                algorithm="ed25519",
                public_key=verify_key.encode(encoder=Base64Encoder).decode(),
                signature=signed.signature.decode(),
            )
            
            return True
            
        except Exception:
            return False
    
    def verify_signature(self) -> bool:
        """
        Verify the envelope signature.
        
        Returns:
            True if signature is valid
        """
        if not HAS_NACL:
            return False
        
        if not self.signature or not self.signature.public_key or not self.signature.signature:
            return False
        
        try:
            verify_key = VerifyKey(
                self.signature.public_key.encode(),
                encoder=Base64Encoder
            )
            
            # Reconstruct payload hash
            payload_json = json.dumps(
                self.payload.to_dict() if hasattr(self.payload, 'to_dict') else self.payload,
                sort_keys=True,
                default=str
            )
            payload_hash = hashlib.sha256(payload_json.encode()).digest()
            
            # Verify
            verify_key.verify(
                payload_hash,
                self.signature.signature.encode(),
                encoder=Base64Encoder
            )
            
            return True
            
        except Exception:
            return False


# ============================================================================
# ENVELOPE FACTORY
# ============================================================================

class EnvelopeFactory:
    """Factory for creating Mycorrhizae envelopes."""
    
    def __init__(
        self,
        device_id: str,
        device_serial: Optional[str] = None,
        source_type: SourceType = SourceType.FCI,
        probe_type: Optional[ProbeType] = None,
        firmware_version: Optional[str] = None,
        location: Optional[GeoLocation] = None,
    ):
        self.source = Source(
            type=source_type,
            device_id=device_id,
            device_serial=device_serial,
            probe_type=probe_type,
            firmware_version=firmware_version,
            location=location,
        )
        self._private_key: Optional[bytes] = None
    
    def set_signing_key(self, private_key_bytes: bytes) -> None:
        """Set the private key for message signing."""
        self._private_key = private_key_bytes
    
    def create_telemetry(
        self,
        bioelectric_channels: List[BioelectricChannelData],
        pattern: PatternData,
        environment: EnvironmentData,
        device_status: Optional[Dict[str, Any]] = None,
    ) -> MycorrhizaeEnvelope:
        """Create an FCI telemetry envelope."""
        payload = FCITelemetryPayload(
            bioelectric_channels=bioelectric_channels,
            pattern=pattern,
            environment=environment,
            device_status=device_status or {},
        )
        
        envelope = MycorrhizaeEnvelope(
            channel=f"device.{self.source.device_id}.telemetry",
            message_type=MessageType.FCI_TELEMETRY,
            source=self.source,
            payload=payload,
        )
        
        if self._private_key:
            envelope.sign(self._private_key)
        
        return envelope
    
    def create_pattern_event(
        self,
        pattern_name: str,
        category: str,
        confidence: float,
        features: Dict[str, Any],
        interpretation: Dict[str, Any],
        duration_ms: float = 0,
        context: Optional[Dict[str, Any]] = None,
    ) -> MycorrhizaeEnvelope:
        """Create a pattern event envelope."""
        payload = PatternEventPayload(
            pattern_name=pattern_name,
            category=category,
            confidence=confidence,
            start_time=datetime.now(timezone.utc),
            duration_ms=duration_ms,
            features=features,
            context=context or {},
            interpretation=interpretation,
        )
        
        envelope = MycorrhizaeEnvelope(
            channel=f"device.{self.source.device_id}.pattern_event",
            message_type=MessageType.PATTERN_EVENT,
            source=self.source,
            payload=payload,
        )
        
        if self._private_key:
            envelope.sign(self._private_key)
        
        return envelope
    
    def create_stimulus_command(
        self,
        waveform: str,
        amplitude_uv: float,
        frequency_hz: float,
        duration_ms: int,
    ) -> MycorrhizaeEnvelope:
        """Create a stimulus command envelope."""
        payload = StimulusCommandPayload(
            waveform=waveform,
            amplitude_uv=amplitude_uv,
            frequency_hz=frequency_hz,
            duration_ms=duration_ms,
        )
        
        envelope = MycorrhizaeEnvelope(
            channel=f"device.{self.source.device_id}.stimulus_command",
            message_type=MessageType.STIMULUS_COMMAND,
            source=self.source,
            payload=payload,
        )
        
        if self._private_key:
            envelope.sign(self._private_key)
        
        return envelope
