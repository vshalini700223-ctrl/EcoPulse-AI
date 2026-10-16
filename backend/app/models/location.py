from typing import Optional
from pydantic import BaseModel, Field
from app.models.common import generate_uuid, get_current_utc_iso


class LocationBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=120, description="Station name (e.g. EcoStation Alpha)")
    zone: str = Field(..., min_length=2, max_length=120, description="Zone description (e.g. Protected Forest Reserve)")
    location_type: str = Field(default="Urban", description="Station ecosystem type (e.g. Forest, Urban, Industrial, Coastal)")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Geographic latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Geographic longitude")
    status: str = Field(default="Active", description="Station status (Active, Maintenance, Offline)")
    active_sensors: int = Field(default=12, ge=0, description="Number of operational sensor probes")
    total_sensors: int = Field(default=12, ge=1, description="Total sensor hardware installed")


class LocationCreate(LocationBase):
    pass


class LocationResponse(LocationBase):
    id: str = Field(default_factory=generate_uuid)
    created_at: str = Field(default_factory=get_current_utc_iso)
    updated_at: str = Field(default_factory=get_current_utc_iso)
    current_aqi: Optional[int] = Field(default=None, description="Latest calculated AQI reading")
    current_status: Optional[str] = Field(default="Nominal", description="Latest environmental assessment")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "loc-alpha-901",
                "name": "EcoStation Alpha — Green Valley Forest",
                "zone": "Protected Ecological Reserve",
                "location_type": "Forest & Watershed",
                "latitude": 12.9352,
                "longitude": 77.5349,
                "status": "Active",
                "active_sensors": 12,
                "total_sensors": 12,
                "created_at": "2026-10-01T00:00:00Z",
                "updated_at": "2026-10-03T09:00:00Z",
                "current_aqi": 32,
                "current_status": "Good"
            }
        }
    }
