from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from app.models.common import generate_uuid, get_current_utc_iso


class MetricThreshold(BaseModel):
    warning: float = Field(..., description="Warning threshold limit")
    critical: float = Field(..., description="Critical threshold limit")
    unit: str = Field(..., description="Unit of measurement (e.g. µg/m³, ppm, °C, %)")
    comparison: str = Field(default="gt", description="Comparison operator: gt (greater than), lt (less than)")


class AlertThresholdConfig(BaseModel):
    pm25: MetricThreshold = Field(
        default_factory=lambda: MetricThreshold(warning=35.0, critical=75.0, unit="µg/m³", comparison="gt")
    )
    pm10: MetricThreshold = Field(
        default_factory=lambda: MetricThreshold(warning=50.0, critical=150.0, unit="µg/m³", comparison="gt")
    )
    aqi: MetricThreshold = Field(
        default_factory=lambda: MetricThreshold(warning=100.0, critical=200.0, unit="AQI Index", comparison="gt")
    )
    co2: MetricThreshold = Field(
        default_factory=lambda: MetricThreshold(warning=800.0, critical=1500.0, unit="ppm", comparison="gt")
    )
    temperature: MetricThreshold = Field(
        default_factory=lambda: MetricThreshold(warning=38.0, critical=45.0, unit="°C", comparison="gt")
    )
    humidity: MetricThreshold = Field(
        default_factory=lambda: MetricThreshold(warning=85.0, critical=95.0, unit="%", comparison="gt")
    )


class AlertBase(BaseModel):
    location_id: str = Field(..., description="ID of location triggering the alert")
    title: str = Field(..., min_length=3, max_length=150, description="Short summary of alert condition")
    severity: str = Field(default="warning", description="Severity level: critical, warning, info")
    metric_name: str = Field(..., description="Environmental parameter (e.g. PM2.5, Humidity, AQI, CO2)")
    metric_value: str = Field(..., description="Measured telemetry value (e.g. 58.4 µg/m³)")
    threshold_description: str = Field(..., description="Regulatory or preset limit exceeded")
    status: str = Field(default="Active", description="Current alert lifecycle state: Active, Acknowledged, Resolved")


class AlertCreate(AlertBase):
    pass


class AlertAcknowledgeRequest(BaseModel):
    notes: Optional[str] = Field(default=None, description="Optional acknowledgement notes")


class AlertResolveRequest(BaseModel):
    resolution_notes: Optional[str] = Field(default=None, description="Corrective actions taken to resolve incident")


class AlertResponse(AlertBase):
    id: str = Field(default_factory=generate_uuid)
    created_at: str = Field(default_factory=get_current_utc_iso)
    location_name: Optional[str] = Field(default=None, description="Resolved station name")
    acknowledged_at: Optional[str] = Field(default=None, description="Timestamp when alert was acknowledged")
    acknowledged_by: Optional[str] = Field(default=None, description="Username of operator acknowledging the alert")
    resolved_at: Optional[str] = Field(default=None, description="Timestamp when alert was resolved")
    resolved_by: Optional[str] = Field(default=None, description="Username of operator resolving the alert")
    resolution_notes: Optional[str] = Field(default=None, description="Notes on resolution actions")
    duplicate_count: int = Field(default=0, description="Number of duplicate alerts prevented for this incident")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "alt-904",
                "location_id": "station-gamma",
                "location_name": "EcoStation Gamma — Industrial Corridor",
                "title": "Elevated PM2.5 Concentration",
                "severity": "warning",
                "metric_name": "PM2.5",
                "metric_value": "58.4 µg/m³",
                "threshold_description": "Exceeded 35.0 µg/m³ threshold",
                "status": "Active",
                "created_at": "2026-10-03T09:20:00Z",
                "acknowledged_at": None,
                "acknowledged_by": None,
                "resolved_at": None,
                "resolved_by": None,
                "resolution_notes": None,
                "duplicate_count": 0
            }
        }
    }


class AlertStatsResponse(BaseModel):
    total: int
    active: int
    acknowledged: int
    resolved: int
    critical: int
    warning: int
    info: int
