"""
USGS Earthquake API Client

Fetches earthquake data from USGS for correlation with M-Wave signals.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
import math

import httpx


@dataclass
class Earthquake:
    """Earthquake event from USGS."""
    id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Location
    latitude: float = 0.0
    longitude: float = 0.0
    depth_km: float = 0.0
    
    # Magnitude
    magnitude: float = 0.0
    magnitude_type: str = "ml"
    
    # Place/region
    place: str = ""
    
    # Significance and intensity
    significance: int = 0  # 0-1000
    felt_reports: int = 0
    cdi: Optional[float] = None  # Community Decimal Intensity
    mmi: Optional[float] = None  # Modified Mercalli Intensity
    
    # Tsunami and alert
    tsunami: bool = False
    alert: Optional[str] = None  # green, yellow, orange, red
    
    # Source
    source: str = "usgs"
    url: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "location": {
                "latitude": self.latitude,
                "longitude": self.longitude,
                "depth_km": self.depth_km,
            },
            "magnitude": self.magnitude,
            "magnitude_type": self.magnitude_type,
            "place": self.place,
            "significance": self.significance,
            "tsunami": self.tsunami,
            "alert": self.alert,
            "url": self.url,
        }


class USGSClient:
    """
    Client for USGS Earthquake API.
    
    Fetches earthquake data for correlation with M-Wave signals.
    API documentation: https://earthquake.usgs.gov/fdsnws/event/1/
    """
    
    BASE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 300  # 5 minutes
        self._cache_time: Dict[str, datetime] = {}
    
    async def get_recent_earthquakes(
        self,
        min_magnitude: float = 2.5,
        days: int = 7,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        max_radius_km: float = 1000,
        limit: int = 100,
    ) -> List[Earthquake]:
        """
        Fetch recent earthquakes from USGS.
        
        Args:
            min_magnitude: Minimum magnitude to include
            days: Number of days to look back
            latitude: Center latitude for radius search
            longitude: Center longitude for radius search
            max_radius_km: Maximum radius in km for search
            limit: Maximum number of results
        
        Returns:
            List of Earthquake objects
        """
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)
        
        params = {
            "format": "geojson",
            "starttime": start_time.isoformat(),
            "endtime": end_time.isoformat(),
            "minmagnitude": min_magnitude,
            "orderby": "time",
            "limit": limit,
        }
        
        # Add location filter if provided
        if latitude is not None and longitude is not None:
            params["latitude"] = latitude
            params["longitude"] = longitude
            params["maxradiuskm"] = max_radius_km
        
        # Check cache
        cache_key = str(params)
        if cache_key in self._cache:
            cache_time = self._cache_time.get(cache_key)
            if cache_time and (datetime.now(timezone.utc) - cache_time).total_seconds() < self._cache_ttl:
                return self._cache[cache_key]
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            print(f"[USGSClient] Error fetching earthquakes: {e}")
            return []
        
        earthquakes = self._parse_geojson(data)
        
        # Cache results
        self._cache[cache_key] = earthquakes
        self._cache_time[cache_key] = datetime.now(timezone.utc)
        
        return earthquakes
    
    async def get_earthquake_by_id(self, event_id: str) -> Optional[Earthquake]:
        """Fetch a specific earthquake by ID."""
        params = {
            "format": "geojson",
            "eventid": event_id,
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            print(f"[USGSClient] Error fetching earthquake {event_id}: {e}")
            return None
        
        earthquakes = self._parse_geojson(data)
        return earthquakes[0] if earthquakes else None
    
    async def get_significant_earthquakes(self, days: int = 30) -> List[Earthquake]:
        """Fetch significant earthquakes (magnitude 6+ or high significance)."""
        return await self.get_recent_earthquakes(
            min_magnitude=6.0,
            days=days,
            limit=50,
        )
    
    def _parse_geojson(self, data: Dict[str, Any]) -> List[Earthquake]:
        """Parse GeoJSON response into Earthquake objects."""
        earthquakes = []
        
        features = data.get("features", [])
        
        for feature in features:
            props = feature.get("properties", {})
            geometry = feature.get("geometry", {})
            coords = geometry.get("coordinates", [0, 0, 0])
            
            # Parse timestamp (USGS uses milliseconds)
            timestamp = datetime.now(timezone.utc)
            if props.get("time"):
                timestamp = datetime.fromtimestamp(props["time"] / 1000, tz=timezone.utc)
            
            earthquake = Earthquake(
                id=feature.get("id", ""),
                timestamp=timestamp,
                latitude=coords[1] if len(coords) > 1 else 0,
                longitude=coords[0] if len(coords) > 0 else 0,
                depth_km=coords[2] if len(coords) > 2 else 0,
                magnitude=props.get("mag", 0),
                magnitude_type=props.get("magType", "ml"),
                place=props.get("place", ""),
                significance=props.get("sig", 0),
                felt_reports=props.get("felt", 0),
                cdi=props.get("cdi"),
                mmi=props.get("mmi"),
                tsunami=props.get("tsunami", 0) == 1,
                alert=props.get("alert"),
                source="usgs",
                url=props.get("url", ""),
            )
            
            earthquakes.append(earthquake)
        
        return earthquakes
    
    def calculate_distance_km(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """Calculate distance between two points using Haversine formula."""
        R = 6371  # Earth radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    async def find_correlations(
        self,
        anomaly_timestamp: datetime,
        anomaly_location: tuple,
        window_hours: float = 72,
        max_distance_km: float = 500,
    ) -> List[Dict[str, Any]]:
        """
        Find earthquakes that may correlate with an M-Wave anomaly.
        
        Args:
            anomaly_timestamp: When the anomaly was detected
            anomaly_location: (latitude, longitude) of anomaly
            window_hours: Time window to search (before and after)
            max_distance_km: Maximum distance to search
        
        Returns:
            List of potential correlations
        """
        lat, lon = anomaly_location
        
        # Search for earthquakes in time window
        earthquakes = await self.get_recent_earthquakes(
            min_magnitude=2.5,
            days=int(window_hours / 24) + 1,
            latitude=lat,
            longitude=lon,
            max_radius_km=max_distance_km,
        )
        
        correlations = []
        
        for eq in earthquakes:
            # Calculate time difference
            time_diff = (eq.timestamp - anomaly_timestamp).total_seconds() / 3600  # Hours
            
            if abs(time_diff) > window_hours:
                continue
            
            # Calculate distance
            distance = self.calculate_distance_km(lat, lon, eq.latitude, eq.longitude)
            
            if distance > max_distance_km:
                continue
            
            # Calculate correlation strength
            # Closer in time and space = stronger correlation
            time_factor = 1.0 - (abs(time_diff) / window_hours)
            distance_factor = 1.0 - (distance / max_distance_km)
            magnitude_factor = min(1.0, eq.magnitude / 7.0)
            
            correlation_strength = (time_factor * 0.4 + distance_factor * 0.3 + magnitude_factor * 0.3)
            
            correlations.append({
                "earthquake": eq.to_dict(),
                "time_diff_hours": time_diff,
                "is_precursor": time_diff > 0,  # Anomaly came before earthquake
                "distance_km": distance,
                "correlation_strength": correlation_strength,
            })
        
        # Sort by correlation strength
        correlations.sort(key=lambda x: x["correlation_strength"], reverse=True)
        
        return correlations
