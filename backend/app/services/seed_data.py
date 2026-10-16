"""Sample seed data for EcoPulse AI database collections."""

SEED_LOCATIONS = [
  {
    "id": "station-alpha",
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
  },
  {
    "id": "station-beta",
    "name": "EcoStation Beta — Urban Metro Central",
    "zone": "High-Density Commercial",
    "location_type": "Urban Canyon",
    "latitude": 12.9784,
    "longitude": 77.6408,
    "status": "Active",
    "active_sensors": 10,
    "total_sensors": 10,
    "created_at": "2026-10-01T00:00:00Z",
    "updated_at": "2026-10-03T09:00:00Z",
    "current_aqi": 86,
    "current_status": "Moderate"
  },
  {
    "id": "station-gamma",
    "name": "EcoStation Gamma — Industrial Corridor",
    "zone": "Manufacturing & Logistics Hub",
    "location_type": "Heavy Industrial",
    "latitude": 12.8452,
    "longitude": 77.6602,
    "status": "Active",
    "active_sensors": 14,
    "total_sensors": 14,
    "created_at": "2026-10-01T00:00:00Z",
    "updated_at": "2026-10-03T09:00:00Z",
    "current_aqi": 124,
    "current_status": "Unhealthy for Sensitive Groups"
  },
  {
    "id": "station-delta",
    "name": "EcoStation Delta — Coastal Biosphere",
    "zone": "Maritime Estuary",
    "location_type": "Wetland & Coast",
    "latitude": 13.0012,
    "longitude": 77.7214,
    "status": "Active",
    "active_sensors": 12,
    "total_sensors": 12,
    "created_at": "2026-10-01T00:00:00Z",
    "updated_at": "2026-10-03T09:00:00Z",
    "current_aqi": 41,
    "current_status": "Good"
  },
  {
    "id": "station-epsilon",
    "name": "EcoStation Epsilon — Tech Valley Plateau",
    "zone": "Suburban Tech Park",
    "location_type": "Suburban",
    "latitude": 12.9102,
    "longitude": 77.6821,
    "status": "Active",
    "active_sensors": 8,
    "total_sensors": 8,
    "created_at": "2026-10-01T00:00:00Z",
    "updated_at": "2026-10-03T09:00:00Z",
    "current_aqi": 68,
    "current_status": "Moderate"
  }
]

SEED_READINGS = [
  {
    "id": "rdg-001",
    "location_id": "station-alpha",
    "location_name": "EcoStation Alpha — Green Valley Forest",
    "pm25": 7.8,
    "pm10": 16.2,
    "aqi": 32,
    "aqi_category": "Good",
    "temperature": 21.6,
    "humidity": 78.0,
    "co2": 398.0,
    "no2": 14.0,
    "o3": 22.0,
    "co": 0.3,
    "so2": 2.1,
    "recorded_at": "2026-10-03T09:00:00Z"
  },
  {
    "id": "rdg-002",
    "location_id": "station-beta",
    "location_name": "EcoStation Beta — Urban Metro Central",
    "pm25": 29.5,
    "pm10": 58.0,
    "aqi": 86,
    "aqi_category": "Moderate",
    "temperature": 27.1,
    "humidity": 52.0,
    "co2": 442.0,
    "no2": 38.0,
    "o3": 44.0,
    "co": 0.8,
    "so2": 5.4,
    "recorded_at": "2026-10-03T09:00:00Z"
  },
  {
    "id": "rdg-003",
    "location_id": "station-gamma",
    "location_name": "EcoStation Gamma — Industrial Corridor",
    "pm25": 45.2,
    "pm10": 89.6,
    "aqi": 124,
    "aqi_category": "Unhealthy for Sensitive Groups",
    "temperature": 28.8,
    "humidity": 46.0,
    "co2": 512.0,
    "no2": 62.0,
    "o3": 54.0,
    "co": 1.4,
    "so2": 12.8,
    "recorded_at": "2026-10-03T09:00:00Z"
  },
  {
    "id": "rdg-004",
    "location_id": "station-delta",
    "location_name": "EcoStation Delta — Coastal Biosphere",
    "pm25": 10.2,
    "pm10": 22.4,
    "aqi": 41,
    "aqi_category": "Good",
    "temperature": 23.4,
    "humidity": 84.0,
    "co2": 404.0,
    "no2": 18.0,
    "o3": 30.0,
    "co": 0.4,
    "so2": 3.0,
    "recorded_at": "2026-10-03T09:00:00Z"
  },
  {
    "id": "rdg-005",
    "location_id": "station-epsilon",
    "location_name": "EcoStation Epsilon — Tech Valley Plateau",
    "pm25": 22.1,
    "pm10": 44.0,
    "aqi": 68,
    "aqi_category": "Moderate",
    "temperature": 25.3,
    "humidity": 61.0,
    "co2": 418.0,
    "no2": 26.0,
    "o3": 36.0,
    "co": 0.5,
    "so2": 4.1,
    "recorded_at": "2026-10-03T09:00:00Z"
  }
]

SEED_ALERTS = [
  {
    "id": "alt-904",
    "location_id": "station-gamma",
    "location_name": "EcoStation Gamma — Industrial Corridor",
    "title": "Elevated PM2.5 Concentration",
    "severity": "warning",
    "metric_name": "PM2.5",
    "metric_value": "58.4 µg/m³",
    "threshold_description": "Exceeded 45 µg/m³ threshold",
    "status": "Active",
    "created_at": "2026-10-03T09:20:00Z"
  },
  {
    "id": "alt-903",
    "location_id": "station-beta",
    "location_name": "EcoStation Beta — Urban Metro Central",
    "title": "Microclimate Humidity Drop",
    "severity": "info",
    "metric_name": "Relative Humidity",
    "metric_value": "38%",
    "threshold_description": "Below seasonal 45% band",
    "status": "Active",
    "created_at": "2026-10-03T08:45:00Z"
  },
  {
    "id": "alt-902",
    "location_id": "station-alpha",
    "location_name": "EcoStation Alpha — Green Valley Forest",
    "title": "Optical Sensor Calibration Check",
    "severity": "success",
    "metric_name": "Hardware Self-Test",
    "metric_value": "Drift < 0.2%",
    "threshold_description": "Passed baseline calibration check",
    "status": "Resolved",
    "created_at": "2026-10-03T07:15:00Z"
  },
  {
    "id": "alt-901",
    "location_id": "station-gamma",
    "location_name": "EcoStation Gamma — Industrial Corridor",
    "title": "Atmospheric Inversion Anomaly",
    "severity": "critical",
    "metric_name": "AQI Forecast Spike",
    "metric_value": "142 Predicted AQI",
    "threshold_description": "AI model detected 87% thermal trapping risk",
    "status": "Active",
    "created_at": "2026-10-03T06:00:00Z"
  }
]

SEED_PREDICTIONS = [
  {
    "id": "pred-001",
    "location_id": "station-beta",
    "location_name": "EcoStation Beta — Urban Metro Central",
    "horizon_hours": 24,
    "predicted_aqi": 94,
    "predicted_pm25": 33.0,
    "confidence_score": 0.94,
    "model_version": "GradientBoost-v1.2",
    "anomaly_risk": 0.12,
    "generated_at": "2026-10-03T08:00:00Z"
  },
  {
    "id": "pred-002",
    "location_id": "station-gamma",
    "location_name": "EcoStation Gamma — Industrial Corridor",
    "horizon_hours": 48,
    "predicted_aqi": 138,
    "predicted_pm25": 52.4,
    "confidence_score": 0.89,
    "model_version": "GradientBoost-v1.2",
    "anomaly_risk": 0.42,
    "generated_at": "2026-10-03T08:00:00Z"
  }
]

SEED_USERS = [
  {
    "id": "usr-001",
    "username": "sarang.lead",
    "email": "sarang@ecopulse.ai",
    "full_name": "Sarang Environmental Engineer",
    "role": "admin",
    "is_active": True,
    "created_at": "2026-10-01T00:00:00Z"
  },
  {
    "id": "usr-002",
    "username": "telemetry.analyst",
    "email": "analyst@ecopulse.ai",
    "full_name": "Air Quality Telemetry Analyst",
    "role": "environmental_analyst",
    "is_active": True,
    "created_at": "2026-10-01T00:00:00Z"
  }
]
