"""
M-Wave Analyzer - Mycelium Seismic Analysis

Analyzes bioelectric signals from mycelium networks for
earthquake prediction and seismic correlation.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4
import math


class AnomalyType(str, Enum):
    """Types of anomalies detectable in M-Wave signals."""
    IMPEDANCE_SPIKE = "impedance_spike"
    CONDUCTIVITY_DROP = "conductivity_drop"
    SYNCHRONIZED_RESPONSE = "synchronized_response"
    PRECURSOR_PATTERN = "precursor_pattern"
    AFTERSHOCK_PATTERN = "aftershock_pattern"


class RiskLevel(str, Enum):
    """Seismic risk levels."""
    LOW = "low"
    MODERATE = "moderate"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MWaveReading:
    """A reading from an M-Wave sensor."""
    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    device_serial: str = ""
    
    # Location
    latitude: float = 0.0
    longitude: float = 0.0
    depth_cm: float = 0.0  # Sensor depth in soil
    
    # Bioelectric signals
    impedance_ohm: float = 0.0
    conductivity_us: float = 0.0
    voltage_mv: float = 0.0
    
    # Environmental
    soil_moisture: float = 0.0  # 0-1
    temperature_c: float = 0.0
    
    # Signal quality
    quality: float = 1.0
    noise_level: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "device_serial": self.device_serial,
            "location": {
                "latitude": self.latitude,
                "longitude": self.longitude,
                "depth_cm": self.depth_cm,
            },
            "signals": {
                "impedance_ohm": self.impedance_ohm,
                "conductivity_us": self.conductivity_us,
                "voltage_mv": self.voltage_mv,
            },
            "environmental": {
                "soil_moisture": self.soil_moisture,
                "temperature_c": self.temperature_c,
            },
            "quality": self.quality,
        }


@dataclass
class SeismicCorrelation:
    """Correlation between M-Wave signals and seismic events."""
    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Anomaly details
    anomaly_type: AnomalyType = AnomalyType.IMPEDANCE_SPIKE
    anomaly_magnitude: float = 0.0  # Z-score or similar metric
    
    # Temporal correlation
    lead_time_hours: Optional[float] = None  # Hours before seismic event
    lag_time_hours: Optional[float] = None   # Hours after seismic event
    
    # Spatial correlation
    distance_km: float = 0.0
    
    # Seismic event (if known)
    earthquake_magnitude: Optional[float] = None
    earthquake_depth_km: Optional[float] = None
    
    # Prediction metrics
    confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "anomaly_type": self.anomaly_type.value,
            "anomaly_magnitude": self.anomaly_magnitude,
            "lead_time_hours": self.lead_time_hours,
            "distance_km": self.distance_km,
            "earthquake_magnitude": self.earthquake_magnitude,
            "confidence": self.confidence,
        }


class MWaveAnalyzer:
    """
    Analyzer for M-Wave seismic signals.
    
    Processes bioelectric signals from distributed mycelium sensors
    to detect anomalies that may precede seismic events.
    
    Key analysis methods:
    - Impedance spike detection
    - Conductivity drop analysis
    - Synchronized response detection
    - Risk prediction scoring
    """
    
    # Detection thresholds
    IMPEDANCE_SPIKE_THRESHOLD = 2.5  # Standard deviations
    CONDUCTIVITY_DROP_THRESHOLD = -2.0
    SYNC_WINDOW_SECONDS = 60
    SYNC_MIN_DEVICES = 3
    
    # Prediction parameters
    TYPICAL_PRECURSOR_HOURS = (6, 72)  # 6-72 hours before event
    MAX_CORRELATION_DISTANCE_KM = 500
    
    def __init__(self, location: Tuple[float, float] = (0.0, 0.0)):
        """
        Initialize analyzer.
        
        Args:
            location: (latitude, longitude) of the analysis center
        """
        self.center_lat, self.center_lon = location
        self.readings: List[MWaveReading] = []
        self.anomalies: List[Dict[str, Any]] = []
        self.correlations: List[SeismicCorrelation] = []
        self._max_readings = 10000
    
    def add_reading(self, reading: MWaveReading) -> None:
        """Add a reading to the analyzer."""
        self.readings.append(reading)
        if len(self.readings) > self._max_readings:
            self.readings = self.readings[-self._max_readings:]
    
    def analyze(self, window_minutes: int = 60) -> Dict[str, Any]:
        """
        Analyze recent readings for anomalies.
        
        Args:
            window_minutes: Analysis window in minutes
        
        Returns:
            Analysis results including detected anomalies and risk assessment
        """
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
        recent = [r for r in self.readings if r.timestamp >= cutoff]
        
        if len(recent) < 10:
            return {
                "status": "insufficient_data",
                "reading_count": len(recent),
                "anomalies": [],
                "risk_level": RiskLevel.LOW.value,
            }
        
        results = {
            "status": "analyzed",
            "reading_count": len(recent),
            "window_minutes": window_minutes,
            "anomalies": [],
            "risk_level": RiskLevel.LOW.value,
            "risk_score": 0.0,
        }
        
        # Detect impedance spikes
        imp_anomalies = self._detect_impedance_spikes(recent)
        results["anomalies"].extend(imp_anomalies)
        
        # Detect conductivity drops
        cond_anomalies = self._detect_conductivity_drops(recent)
        results["anomalies"].extend(cond_anomalies)
        
        # Detect synchronized responses
        sync_anomalies = self._detect_synchronized_responses(recent)
        results["anomalies"].extend(sync_anomalies)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(results["anomalies"])
        results["risk_score"] = risk_score
        results["risk_level"] = self._score_to_risk_level(risk_score).value
        
        # Store anomalies
        self.anomalies.extend(results["anomalies"])
        
        return results
    
    def _detect_impedance_spikes(self, readings: List[MWaveReading]) -> List[Dict[str, Any]]:
        """Detect impedance spike anomalies."""
        anomalies = []
        
        if len(readings) < 10:
            return anomalies
        
        # Calculate baseline statistics
        values = [r.impedance_ohm for r in readings]
        mean_val = sum(values) / len(values)
        variance = sum((v - mean_val) ** 2 for v in values) / len(values)
        std_val = variance ** 0.5 if variance > 0 else 1.0
        
        for r in readings:
            z_score = (r.impedance_ohm - mean_val) / std_val
            
            if z_score > self.IMPEDANCE_SPIKE_THRESHOLD:
                anomalies.append({
                    "type": AnomalyType.IMPEDANCE_SPIKE.value,
                    "timestamp": r.timestamp.isoformat(),
                    "device_serial": r.device_serial,
                    "value": r.impedance_ohm,
                    "z_score": z_score,
                    "baseline_mean": mean_val,
                    "baseline_std": std_val,
                    "location": {"lat": r.latitude, "lon": r.longitude},
                    "severity": min(1.0, (z_score - self.IMPEDANCE_SPIKE_THRESHOLD) / 3.0),
                })
        
        return anomalies
    
    def _detect_conductivity_drops(self, readings: List[MWaveReading]) -> List[Dict[str, Any]]:
        """Detect conductivity drop anomalies."""
        anomalies = []
        
        if len(readings) < 10:
            return anomalies
        
        values = [r.conductivity_us for r in readings]
        mean_val = sum(values) / len(values)
        variance = sum((v - mean_val) ** 2 for v in values) / len(values)
        std_val = variance ** 0.5 if variance > 0 else 1.0
        
        for r in readings:
            z_score = (r.conductivity_us - mean_val) / std_val
            
            if z_score < self.CONDUCTIVITY_DROP_THRESHOLD:
                anomalies.append({
                    "type": AnomalyType.CONDUCTIVITY_DROP.value,
                    "timestamp": r.timestamp.isoformat(),
                    "device_serial": r.device_serial,
                    "value": r.conductivity_us,
                    "z_score": z_score,
                    "baseline_mean": mean_val,
                    "location": {"lat": r.latitude, "lon": r.longitude},
                    "severity": min(1.0, abs(z_score + self.CONDUCTIVITY_DROP_THRESHOLD) / 3.0),
                })
        
        return anomalies
    
    def _detect_synchronized_responses(self, readings: List[MWaveReading]) -> List[Dict[str, Any]]:
        """Detect synchronized responses across multiple devices."""
        anomalies = []
        
        # Group readings by time window
        window_ms = self.SYNC_WINDOW_SECONDS * 1000
        
        # Group by device
        by_device: Dict[str, List[MWaveReading]] = {}
        for r in readings:
            if r.device_serial not in by_device:
                by_device[r.device_serial] = []
            by_device[r.device_serial].append(r)
        
        if len(by_device) < self.SYNC_MIN_DEVICES:
            return anomalies
        
        # Look for synchronized impedance changes
        # Group readings into time buckets
        time_buckets: Dict[int, List[MWaveReading]] = {}
        for r in readings:
            bucket = int(r.timestamp.timestamp() * 1000 / window_ms)
            if bucket not in time_buckets:
                time_buckets[bucket] = []
            time_buckets[bucket].append(r)
        
        for bucket, bucket_readings in time_buckets.items():
            devices_in_bucket = set(r.device_serial for r in bucket_readings)
            
            if len(devices_in_bucket) >= self.SYNC_MIN_DEVICES:
                # Check if all show similar pattern
                impedance_changes = []
                for device in devices_in_bucket:
                    device_readings = [r for r in bucket_readings if r.device_serial == device]
                    if len(device_readings) >= 2:
                        change = device_readings[-1].impedance_ohm - device_readings[0].impedance_ohm
                        impedance_changes.append(change)
                
                if len(impedance_changes) >= self.SYNC_MIN_DEVICES:
                    # Check if all changes are in same direction
                    positive = sum(1 for c in impedance_changes if c > 0)
                    negative = sum(1 for c in impedance_changes if c < 0)
                    
                    if positive >= self.SYNC_MIN_DEVICES or negative >= self.SYNC_MIN_DEVICES:
                        anomalies.append({
                            "type": AnomalyType.SYNCHRONIZED_RESPONSE.value,
                            "timestamp": bucket_readings[0].timestamp.isoformat(),
                            "devices": list(devices_in_bucket),
                            "device_count": len(devices_in_bucket),
                            "direction": "increase" if positive > negative else "decrease",
                            "avg_change": sum(impedance_changes) / len(impedance_changes),
                            "severity": min(1.0, len(devices_in_bucket) / 10.0),
                        })
        
        return anomalies
    
    def _calculate_risk_score(self, anomalies: List[Dict[str, Any]]) -> float:
        """Calculate overall seismic risk score from anomalies."""
        if not anomalies:
            return 0.0
        
        score = 0.0
        
        for a in anomalies:
            severity = a.get("severity", 0.5)
            
            if a["type"] == AnomalyType.SYNCHRONIZED_RESPONSE.value:
                # Synchronized responses are most concerning
                score += severity * 0.4
            elif a["type"] == AnomalyType.IMPEDANCE_SPIKE.value:
                score += severity * 0.2
            elif a["type"] == AnomalyType.CONDUCTIVITY_DROP.value:
                score += severity * 0.15
        
        return min(1.0, score)
    
    def _score_to_risk_level(self, score: float) -> RiskLevel:
        """Convert risk score to risk level."""
        if score < 0.1:
            return RiskLevel.LOW
        elif score < 0.3:
            return RiskLevel.MODERATE
        elif score < 0.5:
            return RiskLevel.ELEVATED
        elif score < 0.7:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    def predict_epicenter(self, anomalies: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Estimate potential epicenter from anomaly pattern.
        
        Uses triangulation from multiple device locations.
        """
        locations = []
        weights = []
        
        for a in anomalies:
            if "location" in a:
                loc = a["location"]
                severity = a.get("severity", 0.5)
                locations.append((loc["lat"], loc["lon"]))
                weights.append(severity)
        
        if len(locations) < 3:
            return None
        
        # Weighted centroid
        total_weight = sum(weights)
        if total_weight == 0:
            return None
        
        weighted_lat = sum(loc[0] * w for loc, w in zip(locations, weights)) / total_weight
        weighted_lon = sum(loc[1] * w for loc, w in zip(locations, weights)) / total_weight
        
        # Calculate uncertainty radius
        distances = [
            self._haversine_km(weighted_lat, weighted_lon, loc[0], loc[1])
            for loc in locations
        ]
        uncertainty_km = sum(distances) / len(distances) if distances else 0
        
        return {
            "estimated_latitude": weighted_lat,
            "estimated_longitude": weighted_lon,
            "uncertainty_km": uncertainty_km,
            "based_on_devices": len(locations),
            "confidence": min(1.0, len(locations) / 10.0),
        }
    
    def _haversine_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in km."""
        R = 6371  # Earth radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def to_mindex_payload(self) -> Dict[str, Any]:
        """Convert current analysis state to MINDEX submission format."""
        latest_analysis = self.analyze(window_minutes=60)
        
        return {
            "source": "mwave_analyzer",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "center_location": {
                "latitude": self.center_lat,
                "longitude": self.center_lon,
            },
            "reading_count": len(self.readings),
            "analysis": latest_analysis,
            "anomaly_count": len(self.anomalies),
            "correlations": [c.to_dict() for c in self.correlations[-10:]],
        }
