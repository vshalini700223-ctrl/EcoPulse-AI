from typing import Optional, Dict
from pydantic import BaseModel, Field
from app.models.common import get_current_utc_iso


class AnalyticsSummaryResponse(BaseModel):
    total_locations: int = Field(..., description="Total configured monitoring stations")
    active_locations: int = Field(..., description="Currently active monitoring stations")
    total_readings: int = Field(..., description="Total cumulative environmental telemetry records")
    average_aqi: float = Field(..., description="Network-wide average AQI")
    max_aqi: int = Field(..., description="Peak AQI recorded in current dataset")
    average_pm25: float = Field(..., description="Mean PM2.5 particulate level (µg/m³)")
    average_pm10: float = Field(..., description="Mean PM10 particulate level (µg/m³)")
    average_temperature: float = Field(..., description="Mean ambient temperature (°C)")
    average_humidity: float = Field(..., description="Mean relative humidity (%)")
    active_alerts_count: int = Field(..., description="Count of currently active/unresolved alerts")
    environmental_grade: str = Field(..., description="Composite network health grade (e.g. Grade A, Grade B)")
    dominant_pollutant: Optional[str] = Field(default="PM2.5", description="Primary respiratory risk driver")
    location_id: Optional[str] = Field(default=None, description="Station ID if filtered")
    location_name: Optional[str] = Field(default=None, description="Resolved station name if filtered")
    data_freshness_iso: str = Field(default_factory=get_current_utc_iso)
    database_connected: bool = Field(..., description="True if connected to live MongoDB Atlas cluster")
