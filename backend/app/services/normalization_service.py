"""Normalization and Deduplication Service for EcoPulse AI Telemetry.

Normalizes raw environmental readings from external weather APIs, simulated streams,
and historical datasets. Computes EPA standard AQI, standardizes timestamps,
and prevents accidental duplicate ingestion.
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from app.models.common import get_aqi_category, get_current_utc_iso
from app.services.database import db_manager

logger = logging.getLogger("ecopulse.normalization")

# US EPA Standard AQI Breakpoints
# Format: (C_low, C_high, I_low, I_high)
PM25_BREAKPOINTS = [
    (0.0, 12.0, 0, 50),
    (12.1, 35.4, 51, 100),
    (35.5, 55.4, 101, 150),
    (55.5, 150.4, 151, 200),
    (150.5, 250.4, 201, 300),
    (250.5, 350.4, 301, 400),
    (350.5, 500.4, 401, 500),
]

PM10_BREAKPOINTS = [
    (0.0, 54.0, 0, 50),
    (55.0, 154.0, 51, 100),
    (155.0, 254.0, 101, 150),
    (255.0, 354.0, 151, 200),
    (355.0, 424.0, 201, 300),
    (425.0, 504.0, 301, 400),
    (505.0, 604.0, 401, 500),
]


def calculate_sub_index(concentration: float, breakpoints: list) -> int:
    """Calculate EPA sub-index using linear interpolation across breakpoints."""
    conc = max(0.0, float(concentration))
    for c_low, c_high, i_low, i_high in breakpoints:
        if c_low <= conc <= c_high:
            sub = ((i_high - i_low) / (c_high - c_low)) * (conc - c_low) + i_low
            return int(round(sub))
    # If concentration exceeds highest breakpoint, cap at 500
    if conc > breakpoints[-1][1]:
        return 500
    return 0


def calculate_epa_aqi(pm25: float, pm10: float) -> Tuple[int, str]:
    """Calculate overall EPA AQI and descriptor category from PM2.5 and PM10 concentrations."""
    aqi_pm25 = calculate_sub_index(pm25, PM25_BREAKPOINTS)
    aqi_pm10 = calculate_sub_index(pm10, PM10_BREAKPOINTS)
    overall_aqi = max(aqi_pm25, aqi_pm10)
    category = get_aqi_category(overall_aqi)
    return overall_aqi, category


def parse_and_standardize_timestamp(ts: Optional[str]) -> str:
    """Ensure timestamp is valid ISO 8601 UTC string ending in 'Z'."""
    if not ts:
        return get_current_utc_iso()
    try:
        # Handle string like '2026-10-03T09:30:00Z' or without Z or with offset
        cleaned = ts.replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return get_current_utc_iso()


def generate_dedup_hash(location_id: str, recorded_at: str, source_type: str) -> str:
    """Create a deterministic SHA-256 fingerprint for deduplication.
    Rounds to nearest 10-second block to avoid duplicate ingestion from parallel polls.
    """
    try:
        dt = datetime.fromisoformat(recorded_at.replace("Z", "+00:00"))
        # Round seconds to nearest 10 seconds
        rounded_sec = (dt.second // 10) * 10
        norm_time = dt.strftime(f"%Y-%m-%d %H:%M:{rounded_sec:02d}")
    except Exception:
        norm_time = recorded_at[:16]

    raw_key = f"{location_id.strip().lower()}|{norm_time}|{source_type.strip().lower()}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]


class NormalizationService:
    """Central service to validate, normalize, and deduplicate environmental readings."""

    @staticmethod
    def normalize_reading(
        raw: Dict[str, Any],
        source_type: str = "simulated",
        source_provider: Optional[str] = None,
        retrieved_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Normalize raw incoming telemetry readings into EcoPulse AI standard format."""
        location_id = str(raw.get("location_id", "station-alpha")).strip()

        # Sanitize and clamp numeric measurements within physically valid bounds
        pm25 = max(0.0, min(1000.0, float(raw.get("pm25", 0.0))))
        pm10 = max(0.0, min(2000.0, float(raw.get("pm10", 0.0))))
        temperature = max(-50.0, min(65.0, float(raw.get("temperature", 25.0))))
        humidity = max(0.0, min(100.0, float(raw.get("humidity", 50.0))))

        # Optional trace gases
        co2 = float(raw["co2"]) if raw.get("co2") is not None else None
        no2 = float(raw["no2"]) if raw.get("no2") is not None else None
        o3 = float(raw["o3"]) if raw.get("o3") is not None else None
        co = float(raw["co"]) if raw.get("co") is not None else None
        so2 = float(raw["so2"]) if raw.get("so2") is not None else None

        # Calculate or validate AQI
        if "aqi" in raw and raw["aqi"] is not None and int(raw["aqi"]) > 0:
            aqi = int(raw["aqi"])
            aqi_category = raw.get("aqi_category") or get_aqi_category(aqi)
        else:
            aqi, aqi_category = calculate_epa_aqi(pm25, pm10)

        # Standardize timestamps
        recorded_at = parse_and_standardize_timestamp(
            raw.get("recorded_at") or raw.get("timestamp")
        )
        retrieval_timestamp = retrieved_at or get_current_utc_iso()

        # Compute deduplication hash
        dedup_hash = generate_dedup_hash(location_id, recorded_at, source_type)

        normalized = {
            "location_id": location_id,
            "pm25": round(pm25, 2),
            "pm10": round(pm10, 2),
            "aqi": aqi,
            "aqi_category": aqi_category,
            "temperature": round(temperature, 1),
            "humidity": round(humidity, 1),
            "co2": round(co2, 1) if co2 is not None else None,
            "no2": round(no2, 2) if no2 is not None else None,
            "o3": round(o3, 2) if o3 is not None else None,
            "co": round(co, 2) if co is not None else None,
            "so2": round(so2, 2) if so2 is not None else None,
            "source_type": source_type,
            "source_provider": source_provider,
            "retrieved_at": retrieval_timestamp,
            "recorded_at": recorded_at,
            "dedup_hash": dedup_hash,
        }
        return normalized

    @staticmethod
    async def is_duplicate(
        location_id: str,
        recorded_at: str,
        source_type: str,
        dedup_hash: Optional[str] = None,
        window_seconds: int = 30,
    ) -> Tuple[bool, Optional[str]]:
        """Check if an identical reading exists within the deduplication window.
        Returns (is_duplicate, existing_record_id).
        """
        target_hash = dedup_hash or generate_dedup_hash(location_id, recorded_at, source_type)

        # 1. Check MongoDB Atlas if connected
        if db_manager.is_connected and db_manager.environmental_readings is not None:
            try:
                # Query by dedup_hash first (exact match)
                existing = await db_manager.environmental_readings.find_one(
                    {"location_id": location_id, "dedup_hash": target_hash},
                    {"id": 1, "_id": 0},
                )
                if existing:
                    return True, existing.get("id")

                # Secondary query: exact same location and recorded_at
                exact_time = await db_manager.environmental_readings.find_one(
                    {"location_id": location_id, "recorded_at": recorded_at, "source_type": source_type},
                    {"id": 1, "_id": 0},
                )
                if exact_time:
                    return True, exact_time.get("id")
            except Exception as e:
                logger.warning(f"Database error during dedup check: {e}")

        # 2. Check in-memory store
        memory_readings = db_manager.memory_store.get("environmental_readings", [])
        for r in memory_readings:
            if r.get("location_id") == location_id and r.get("source_type") == source_type:
                # Check hash
                if r.get("dedup_hash") and r.get("dedup_hash") == target_hash:
                    return True, r.get("id")
                # Check exact timestamp
                if r.get("recorded_at") == recorded_at:
                    return True, r.get("id")

        return False, None


normalizer = NormalizationService()
