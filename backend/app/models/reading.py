from typing import List, Optional
from pydantic import BaseModel, Field, model_validator
from app.models.common import generate_uuid, get_current_utc_iso, get_aqi_category


class ReadingBase(BaseModel):
    location_id: str = Field(..., description="ID or slug of the monitoring location")
    pm25: float = Field(..., ge=0.0, le=1000.0, description="PM2.5 particulate concentration in µg/m³")
    pm10: float = Field(..., ge=0.0, le=2000.0, description="PM10 particulate concentration in µg/m³")
    aqi: int = Field(..., ge=0, le=500, description="Calculated Air Quality Index (0-500)")
    temperature: float = Field(..., ge=-60.0, le=70.0, description="Ambient temperature in °C")
    humidity: float = Field(..., ge=0.0, le=100.0, description="Relative humidity percentage")
    co2: Optional[float] = Field(default=None, ge=200.0, le=5000.0, description="CO2 concentration in ppm")
    no2: Optional[float] = Field(default=None, ge=0.0, le=1000.0, description="NO2 concentration in ppb")
    o3: Optional[float] = Field(default=None, ge=0.0, le=1000.0, description="Ozone concentration in ppb")
    co: Optional[float] = Field(default=None, ge=0.0, le=200.0, description="Carbon monoxide in ppm")
    so2: Optional[float] = Field(default=None, ge=0.0, le=1000.0, description="Sulfur dioxide in ppb")
    aqi_category: Optional[str] = Field(default=None, description="Air quality descriptor (Good, Moderate, etc.)")
    source_type: str = Field(default="simulated", description="Data origin: 'real', 'simulated', or 'historical'")
    source_provider: Optional[str] = Field(default=None, description="Provider identifier (e.g. 'open-meteo', 'openweather', 'simulator')")
    retrieved_at: Optional[str] = Field(default=None, description="Timestamp when data was retrieved from source")
    dedup_hash: Optional[str] = Field(default=None, description="Deterministic hash for duplicate prevention")


class ReadingCreate(ReadingBase):
    timestamp: Optional[str] = Field(default=None, description="Reading timestamp in ISO format (defaults to now)")

    @model_validator(mode="after")
    def populate_category_and_timestamp(self):
        if not self.aqi_category:
            self.aqi_category = get_aqi_category(self.aqi)
        if not self.timestamp:
            self.timestamp = get_current_utc_iso()
        return self


class ReadingResponse(ReadingBase):
    id: str = Field(default_factory=generate_uuid)
    recorded_at: str = Field(default_factory=get_current_utc_iso)
    location_name: Optional[str] = Field(default=None, description="Resolved human-readable station name")
    is_duplicate: Optional[bool] = Field(default=False, description="Flag indicating if record was a duplicate")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "rdg-771829",
                "location_id": "station-beta",
                "location_name": "EcoStation Beta — Urban Metro Central",
                "pm25": 28.4,
                "pm10": 56.1,
                "aqi": 82,
                "aqi_category": "Moderate",
                "temperature": 26.5,
                "humidity": 58.0,
                "co2": 435.0,
                "no2": 32.0,
                "o3": 28.0,
                "source_type": "real",
                "source_provider": "open-meteo",
                "retrieved_at": "2026-10-03T09:30:00Z",
                "recorded_at": "2026-10-03T09:30:00Z"
            }
        }
    }


class PaginatedReadingsResponse(BaseModel):
    total: int = Field(..., description="Total matching telemetry records in collection")
    page: int = Field(..., description="Current page index (1-indexed)")
    limit: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total pages available")
    items: List[ReadingResponse] = Field(default_factory=list, description="List of environmental readings")


class IngestionResult(BaseModel):
    status: str = Field(..., description="'success', 'duplicate_skipped', or 'error'")
    is_duplicate: bool = Field(default=False)
    reading: Optional[ReadingResponse] = None
    message: str = Field(default="")


class BatchIngestionResponse(BaseModel):
    status: str = Field(default="completed")
    total_submitted: int = 0
    ingested_count: int = 0
    duplicates_skipped: int = 0
    errors_count: int = 0
    details: List[str] = Field(default_factory=list)


class HistoricalSummaryResponse(BaseModel):
    location_id: Optional[str] = None
    source_type: Optional[str] = None
    total_records: int = 0
    average_aqi: Optional[float] = None
    min_aqi: Optional[int] = None
    max_aqi: Optional[int] = None
    average_pm25: Optional[float] = None
    average_pm10: Optional[float] = None
    average_temperature: Optional[float] = None
    average_humidity: Optional[float] = None
    items: List[ReadingResponse] = Field(default_factory=list)
