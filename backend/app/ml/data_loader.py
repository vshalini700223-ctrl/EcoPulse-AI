"""Data loading, timestamp validation, and missing value handling for EcoPulse AI ML pipeline.

Ensures strict chronological consistency with zero future leakage.
"""

import os
import csv
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger("ecopulse.ml.data_loader")

DEFAULT_DATASET_PATH = Path(__file__).parent / "data" / "sample_environmental_data.csv"

# Physical and regulatory validation bounds
VALID_BOUNDS = {
    "pm25": (0.0, 1000.0),
    "pm10": (0.0, 1500.0),
    "aqi": (0, 500),
    "temperature": (-40.0, 60.0),
    "humidity": (0.0, 100.0),
    "co2": (200.0, 5000.0),
    "no2": (0.0, 500.0),
    "o3": (0.0, 600.0),
}


class EnvironmentalRecord:
    """Strongly typed container for validated environmental time-series records."""
    __slots__ = (
        "timestamp",
        "location_id",
        "location_name",
        "pm25",
        "pm10",
        "aqi",
        "temperature",
        "humidity",
        "co2",
        "no2",
        "o3",
        "source_type",
    )

    def __init__(
        self,
        timestamp: datetime,
        location_id: str,
        location_name: str,
        pm25: float,
        pm10: Optional[float] = None,
        aqi: Optional[int] = None,
        temperature: Optional[float] = None,
        humidity: Optional[float] = None,
        co2: Optional[float] = None,
        no2: Optional[float] = None,
        o3: Optional[float] = None,
        source_type: str = "historical",
    ):
        self.timestamp = timestamp
        self.location_id = location_id
        self.location_name = location_name
        self.pm25 = pm25
        self.pm10 = pm10
        self.aqi = aqi
        self.temperature = temperature
        self.humidity = humidity
        self.co2 = co2
        self.no2 = no2
        self.o3 = o3
        self.source_type = source_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "location_id": self.location_id,
            "location_name": self.location_name,
            "pm25": self.pm25,
            "pm10": self.pm10,
            "aqi": self.aqi,
            "temperature": self.temperature,
            "humidity": self.humidity,
            "co2": self.co2,
            "no2": self.no2,
            "o3": self.o3,
            "source_type": self.source_type,
        }


def parse_iso_timestamp(ts_str: Any) -> Optional[datetime]:
    """Parse various ISO timestamp formats safely into UTC datetime."""
    if isinstance(ts_str, datetime):
        if ts_str.tzinfo is None:
            return ts_str.replace(tzinfo=timezone.utc)
        return ts_str.astimezone(timezone.utc)

    if not ts_str or not isinstance(ts_str, str):
        return None

    clean_str = ts_str.strip()
    if clean_str.endswith("Z"):
        clean_str = clean_str[:-1] + "+00:00"

    try:
        dt = datetime.fromisoformat(clean_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        # Fallback to standard strptime
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(clean_str[:19], fmt).replace(tzinfo=timezone.utc)
                return dt
            except Exception:
                pass
    return None


def validate_and_clean_value(val: Any, bounds: Tuple[float, float], default: Optional[float] = None) -> Optional[float]:
    """Check numerical range; clip extreme errors or substitute safe bounds."""
    if val is None or val == "":
        return default
    try:
        num = float(val)
        min_v, max_v = bounds
        if num < min_v:
            return min_v
        if num > max_v:
            return max_v
        return round(num, 2)
    except (ValueError, TypeError):
        return default


class EnvironmentalDataLoader:
    """Loads and validates environmental telemetry from CSV or DB sources."""

    @classmethod
    def load_from_csv(
        cls,
        csv_path: Optional[str] = None,
        location_id: Optional[str] = None,
    ) -> List[EnvironmentalRecord]:
        """Load records from a documented CSV file, validate timestamps, and clean missing values."""
        target_path = Path(csv_path) if csv_path else DEFAULT_DATASET_PATH
        if not target_path.exists():
            raise FileNotFoundError(f"Sample environmental dataset not found at {target_path}")

        raw_records = []
        with open(target_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if location_id and row.get("location_id") != location_id:
                    continue
                raw_records.append(row)

        return cls.validate_and_impute_series(raw_records)

    @classmethod
    def load_from_records(
        cls,
        records: List[Dict[str, Any]],
        location_id: Optional[str] = None,
    ) -> List[EnvironmentalRecord]:
        """Validate and clean in-memory dictionary records (from API or MongoDB)."""
        filtered = [
            r for r in records
            if not location_id or r.get("location_id") == location_id
        ]
        return cls.validate_and_impute_series(filtered)

    @classmethod
    def validate_and_impute_series(cls, raw_list: List[Dict[str, Any]]) -> List[EnvironmentalRecord]:
        """Validates timestamps and numerical bounds, and applies causal forward-fill imputation.
        
        Strict Rule: Never use future information to impute missing past entries.
        """
        parsed: List[Dict[str, Any]] = []

        for r in raw_list:
            raw_ts = r.get("timestamp") or r.get("recorded_at")
            ts = parse_iso_timestamp(raw_ts)
            if ts is None:
                continue

            pm25 = validate_and_clean_value(r.get("pm25"), VALID_BOUNDS["pm25"])
            if pm25 is None:
                # If initial PM2.5 missing, placeholder for forward-fill
                pm25 = None

            parsed.append({
                "ts": ts,
                "location_id": r.get("location_id", "station-alpha"),
                "location_name": r.get("location_name") or r.get("location_id", "Monitoring Station"),
                "pm25": pm25,
                "pm10": validate_and_clean_value(r.get("pm10"), VALID_BOUNDS["pm10"]),
                "aqi": int(validate_and_clean_value(r.get("aqi"), VALID_BOUNDS["aqi"], default=50) or 50),
                "temperature": validate_and_clean_value(r.get("temperature"), VALID_BOUNDS["temperature"], default=24.0),
                "humidity": validate_and_clean_value(r.get("humidity"), VALID_BOUNDS["humidity"], default=60.0),
                "co2": validate_and_clean_value(r.get("co2"), VALID_BOUNDS["co2"], default=420.0),
                "no2": validate_and_clean_value(r.get("no2"), VALID_BOUNDS["no2"], default=20.0),
                "o3": validate_and_clean_value(r.get("o3"), VALID_BOUNDS["o3"], default=25.0),
                "source_type": r.get("source_type", "historical"),
            })

        # Sort chronologically by timestamp
        parsed.sort(key=lambda x: x["ts"])

        # Deduplicate identical timestamps per station (keep latest)
        deduped: Dict[Tuple[str, datetime], Dict[str, Any]] = {}
        for item in parsed:
            key = (item["location_id"], item["ts"])
            deduped[key] = item

        sorted_items = sorted(deduped.values(), key=lambda x: x["ts"])

        # Forward-fill missing values along chronological order per location (causal, no future leakage)
        cleaned_records: List[EnvironmentalRecord] = []
        last_seen_pm25_by_loc: Dict[str, float] = {}

        for item in sorted_items:
            loc = item["location_id"]
            pm25_val = item["pm25"]

            if pm25_val is None:
                # Forward-fill from previous known reading if available
                if loc in last_seen_pm25_by_loc:
                    pm25_val = last_seen_pm25_by_loc[loc]
                else:
                    # Fallback to conservative baseline default
                    pm25_val = 25.0
            else:
                last_seen_pm25_by_loc[loc] = pm25_val

            # Ensure pm10 and aqi are consistent
            pm10_val = item["pm10"] or round(pm25_val * 1.5, 1)
            aqi_val = item["aqi"] or int(round(pm25_val * 2.1))

            cleaned_records.append(
                EnvironmentalRecord(
                    timestamp=item["ts"],
                    location_id=loc,
                    location_name=item["location_name"],
                    pm25=pm25_val,
                    pm10=pm10_val,
                    aqi=aqi_val,
                    temperature=item["temperature"],
                    humidity=item["humidity"],
                    co2=item["co2"],
                    no2=item["no2"],
                    o3=item["o3"],
                    source_type=item["source_type"],
                )
            )

        return cleaned_records
