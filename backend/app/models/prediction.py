from typing import Optional
from pydantic import BaseModel, Field
from app.models.common import generate_uuid, get_current_utc_iso


class PredictionCreate(BaseModel):
    location_id: str = Field(..., description="ID of location prediction applies to")
    horizon_hours: int = Field(..., ge=1, le=168, description="Prediction horizon in hours forward")
    predicted_aqi: int = Field(..., ge=0, le=500, description="Predicted AQI value")
    predicted_pm25: Optional[float] = Field(default=None, description="Predicted PM2.5 level")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Model confidence score between 0.0 and 1.0")
    model_version: str = Field(default="GradientBoost-v1.2", description="Model architecture identifier")
    anomaly_risk: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Inversion anomaly risk probability")


class PredictionResponse(PredictionCreate):
    id: str = Field(default_factory=generate_uuid)
    generated_at: str = Field(default_factory=get_current_utc_iso)
    location_name: Optional[str] = Field(default=None)
