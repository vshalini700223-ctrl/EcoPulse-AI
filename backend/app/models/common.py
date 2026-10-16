import uuid
from datetime import datetime, timezone


def generate_uuid() -> str:
    """Generate a clean UUID4 string."""
    return str(uuid.uuid4())


def get_current_utc_iso() -> str:
    """Return current UTC time in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def get_aqi_category(aqi: int) -> str:
    """Classify AQI value into standard EPA categories."""
    if aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Moderate"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    elif aqi <= 200:
        return "Unhealthy"
    elif aqi <= 300:
        return "Very Unhealthy"
    else:
        return "Hazardous"
