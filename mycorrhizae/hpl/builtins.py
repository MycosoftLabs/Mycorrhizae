"""
HPL Builtins - Built-in Functions for Hypha Programming Language

Provides sensor integration, signal emission, and biological metaphors.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID


@dataclass
class SensorReading:
    """A reading from a sensor."""
    sensor_id: str
    timestamp: datetime
    value: float
    unit: str
    quality: float = 1.0  # 0-1 confidence
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SensorContext:
    """
    Context for sensor operations in HPL.
    
    Provides access to sensor data from MycoBrain devices.
    """
    device_serial: str
    sensors: Dict[str, SensorReading] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    outputs: List[Dict[str, Any]] = field(default_factory=list)
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    
    def update_sensor(self, sensor_id: str, value: float, unit: str, quality: float = 1.0) -> None:
        """Update a sensor reading."""
        self.sensors[sensor_id] = SensorReading(
            sensor_id=sensor_id,
            timestamp=datetime.now(timezone.utc),
            value=value,
            unit=unit,
            quality=quality,
        )
    
    def get_sensor(self, sensor_id: str) -> Optional[SensorReading]:
        """Get a sensor reading."""
        return self.sensors.get(sensor_id)
    
    def set_variable(self, name: str, value: Any) -> None:
        """Set a variable in the context."""
        self.variables[name] = value
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a variable from the context."""
        return self.variables.get(name, default)


class HPLBuiltins:
    """
    Built-in functions for HPL.
    
    Biological metaphors:
    - sense: Read sensor data
    - emit: Output signal to channel
    - branch: Conditional based on sensor thresholds
    - grow: Accumulate values over time
    - fruit: Produce final output
    - decay: Clean up resources
    """
    
    def __init__(self, context: SensorContext, emit_callback: Optional[Callable] = None):
        self.context = context
        self.emit_callback = emit_callback
        self._accumulators: Dict[str, List[float]] = {}
    
    # ==================== Core Builtins ====================
    
    def sense(self, sensor_id: str, field: str = "value") -> Optional[float]:
        """
        Sense (read) a value from a sensor.
        
        Usage in HPL:
            hypha temp = sense("temperature")
            hypha quality = sense("impedance", "quality")
        """
        reading = self.context.get_sensor(sensor_id)
        if not reading:
            return None
        
        if field == "value":
            return reading.value
        elif field == "quality":
            return reading.quality
        elif field == "timestamp":
            return reading.timestamp.timestamp()
        else:
            return reading.metadata.get(field)
    
    def emit(self, channel: str, payload: Dict[str, Any], message_type: str = "telemetry") -> None:
        """
        Emit a signal to a channel.
        
        Usage in HPL:
            emit("alerts", {"type": "threshold_exceeded", "value": temp})
        """
        output = {
            "channel": f"device.{self.context.device_serial}.{channel}",
            "message_type": message_type,
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        self.context.outputs.append(output)
        
        if self.emit_callback:
            self.emit_callback(output)
    
    def branch(self, condition: bool, true_value: Any, false_value: Any = None) -> Any:
        """
        Conditional branching.
        
        Usage in HPL:
            branch(temp > 30, emit("alerts", {"hot": true}))
        """
        if condition:
            return true_value
        return false_value
    
    def grow(self, name: str, value: float, max_size: int = 100) -> List[float]:
        """
        Accumulate values over time (like mycelium growing).
        
        Usage in HPL:
            grow("temp_history", temp)
        """
        if name not in self._accumulators:
            self._accumulators[name] = []
        
        self._accumulators[name].append(value)
        
        # Keep only last max_size values
        if len(self._accumulators[name]) > max_size:
            self._accumulators[name] = self._accumulators[name][-max_size:]
        
        return self._accumulators[name]
    
    def fruit(self, name: str, value: Any) -> Dict[str, Any]:
        """
        Produce a final output (like mushroom fruiting).
        
        Usage in HPL:
            fruit("analysis_result", {"status": "healthy"})
        """
        output = {
            "name": name,
            "value": value,
            "device": self.context.device_serial,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        self.context.outputs.append(output)
        return output
    
    def decay(self, name: str) -> None:
        """
        Clean up resources (like fungal decomposition).
        
        Usage in HPL:
            decay("temp_history")
        """
        if name in self._accumulators:
            del self._accumulators[name]
        
        if name in self.context.variables:
            del self.context.variables[name]
    
    # ==================== Statistical Builtins ====================
    
    def avg(self, name: str) -> Optional[float]:
        """Get average of accumulated values."""
        values = self._accumulators.get(name, [])
        if not values:
            return None
        return sum(values) / len(values)
    
    def min_val(self, name: str) -> Optional[float]:
        """Get minimum of accumulated values."""
        values = self._accumulators.get(name, [])
        if not values:
            return None
        return min(values)
    
    def max_val(self, name: str) -> Optional[float]:
        """Get maximum of accumulated values."""
        values = self._accumulators.get(name, [])
        if not values:
            return None
        return max(values)
    
    def stddev(self, name: str) -> Optional[float]:
        """Get standard deviation of accumulated values."""
        values = self._accumulators.get(name, [])
        if len(values) < 2:
            return None
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5
    
    def trend(self, name: str) -> Optional[str]:
        """Detect trend in accumulated values."""
        values = self._accumulators.get(name, [])
        if len(values) < 3:
            return None
        
        recent = values[-3:]
        if recent[-1] > recent[0]:
            return "increasing"
        elif recent[-1] < recent[0]:
            return "decreasing"
        return "stable"
    
    # ==================== Alert Builtins ====================
    
    def alert(
        self,
        level: str,
        message: str,
        sensor_id: Optional[str] = None,
        threshold: Optional[float] = None,
        value: Optional[float] = None,
    ) -> None:
        """
        Emit an alert.
        
        Levels: info, warning, critical
        """
        alert = {
            "level": level,
            "message": message,
            "device": self.context.device_serial,
            "sensor_id": sensor_id,
            "threshold": threshold,
            "value": value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        self.context.alerts.append(alert)
        self.emit("alerts", alert, message_type="event")
    
    def threshold_check(
        self,
        sensor_id: str,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        alert_level: str = "warning",
    ) -> bool:
        """
        Check sensor value against thresholds.
        
        Returns True if within bounds, False if alert triggered.
        """
        reading = self.context.get_sensor(sensor_id)
        if not reading:
            return True
        
        value = reading.value
        
        if min_val is not None and value < min_val:
            self.alert(
                alert_level,
                f"{sensor_id} below minimum ({value} < {min_val})",
                sensor_id=sensor_id,
                threshold=min_val,
                value=value,
            )
            return False
        
        if max_val is not None and value > max_val:
            self.alert(
                alert_level,
                f"{sensor_id} above maximum ({value} > {max_val})",
                sensor_id=sensor_id,
                threshold=max_val,
                value=value,
            )
            return False
        
        return True
    
    # ==================== Utility Builtins ====================
    
    def log(self, message: str, level: str = "info") -> None:
        """Log a message."""
        print(f"[HPL:{level.upper()}] {message}")
    
    def now(self) -> float:
        """Get current timestamp."""
        return datetime.now(timezone.utc).timestamp()
    
    def elapsed(self, sensor_id: str) -> Optional[float]:
        """Get seconds since last sensor reading."""
        reading = self.context.get_sensor(sensor_id)
        if not reading:
            return None
        
        return (datetime.now(timezone.utc) - reading.timestamp).total_seconds()
