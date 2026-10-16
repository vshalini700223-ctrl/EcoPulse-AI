"""Historical Environmental Datasets Service for EcoPulse AI.

Provides multi-day historical telemetry datasets for analytics, machine learning
model training, and predictive baseline evaluation without physical sensors.
Strictly marks all records with source_type = 'historical'.
"""

import math
import random
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
import httpx
from app.models.common import generate_uuid
from app.services.database import db_manager
from app.services.normalization_service import normalizer
from app.services.simulation_service import STATION_PROFILES, DEFAULT_PROFILE

logger = logging.getLogger("ecopulse.historical")


class HistoricalDatasetService:
    """Provides and seeds historical environmental telemetry time-series."""

    @staticmethod
    def generate_historical_records(
        station_id: str,
        days: int = 7,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Synthesize realistic multi-day hourly historical readings for a station.
        Includes diurnal curves, weather weather-front variations, and realistic atmospheric dynamics.
        """
        if end_date is None:
            end_date = datetime.now(timezone.utc)

        start_date = end_date - timedelta(days=days)
        profile = STATION_PROFILES.get(station_id, DEFAULT_PROFILE)
        records: List[Dict[str, Any]] = []

        current_dt = start_date
        total_hours = days * 24

        for step in range(total_hours):
            hour = current_dt.hour + (current_dt.minute / 60.0)
            day_of_week = current_dt.weekday()  # 0=Monday, 6=Sunday

            # Diurnal solar cycle factor
            solar_factor = math.sin((hour - 8.0) * math.pi / 12.0)

            # Weekend traffic reduction factor (lower PM2.5/NO2 on Saturday & Sunday)
            is_weekend = day_of_week >= 5
            traffic_modifier = 0.72 if is_weekend else 1.0

            # Commuter rush hour spike
            rush_hour_boost = 0.0
            if (7.0 <= hour <= 9.5 or 17.5 <= hour <= 20.0) and not is_weekend:
                rush_hour_boost = random.uniform(8.0, 22.0)

            # Atmospheric weather front fluctuation (3-day macro cycle)
            macro_weather_factor = math.sin(step * 2 * math.pi / 72.0) * 2.5

            # Calculate realistic physical parameters
            temp = profile["temp_base"] + (solar_factor * profile["temp_variance"]) + macro_weather_factor + random.uniform(-0.6, 0.6)
            temp = round(max(-10.0, min(50.0, temp)), 1)

            humidity = profile["humidity_base"] - (solar_factor * (profile["humidity_variance"] * 0.7)) - (macro_weather_factor * 1.5) + random.uniform(-2.0, 2.0)
            humidity = round(max(15.0, min(98.0, humidity)), 1)

            pm25 = max(3.0, (profile["pm25_base"] * traffic_modifier) + rush_hour_boost + random.gauss(0, profile["pm25_variance"] * 0.3))
            pm10 = max(pm25 * 1.4, (profile["pm10_base"] * traffic_modifier) + (rush_hour_boost * 1.7) + random.gauss(0, profile["pm10_variance"] * 0.3))
            pm25 = round(pm25, 1)
            pm10 = round(pm10, 1)

            co2 = round(profile["co2_base"] + (rush_hour_boost * 1.8) + random.uniform(-6.0, 8.0), 1)
            no2 = round(max(5.0, (18.0 * traffic_modifier) + (rush_hour_boost * 0.8) + random.uniform(-2.0, 4.0)), 1)
            o3 = round(max(5.0, 24.0 + (solar_factor * 14.0) + random.uniform(-3.0, 3.0)), 1)
            co = round(max(0.1, 0.4 + (rush_hour_boost * 0.02) + random.uniform(-0.04, 0.04)), 2)
            so2 = round(max(1.0, 7.0 + random.uniform(-1.5, 2.5)), 1)

            ts_iso = current_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

            raw_reading = {
                "location_id": station_id,
                "pm25": pm25,
                "pm10": pm10,
                "temperature": temp,
                "humidity": humidity,
                "co2": co2,
                "no2": no2,
                "o3": o3,
                "co": co,
                "so2": so2,
                "recorded_at": ts_iso,
            }

            normalized = normalizer.normalize_reading(
                raw=raw_reading,
                source_type="historical",
                source_provider="cpcb-archive-model",
                retrieved_at=ts_iso,
            )
            normalized["id"] = f"hist-{generate_uuid()[:8]}"
            records.append(normalized)

            current_dt += timedelta(hours=1)

        return records

    @classmethod
    async def seed_historical_data(cls, days: int = 7) -> Dict[str, Any]:
        """Batch seed multi-day historical telemetry into MongoDB or memory store."""
        station_ids = list(STATION_PROFILES.keys())
        total_ingested = 0
        total_duplicates = 0

        for st_id in station_ids:
            records = cls.generate_historical_records(st_id, days=days)
            for rec in records:
                is_dup, _ = await normalizer.is_duplicate(
                    location_id=rec["location_id"],
                    recorded_at=rec["recorded_at"],
                    source_type="historical",
                    dedup_hash=rec.get("dedup_hash"),
                )
                if is_dup:
                    total_duplicates += 1
                    continue

                if db_manager.is_connected and db_manager.environmental_readings is not None:
                    try:
                        await db_manager.environmental_readings.insert_one(dict(rec))
                        total_ingested += 1
                    except Exception as e:
                        logger.warning(f"Error seeding historical record: {e}")
                else:
                    db_manager.memory_store["environmental_readings"].append(rec)
                    total_ingested += 1

        logger.info(f"Historical dataset seeded: {total_ingested} ingested, {total_duplicates} duplicates skipped.")
        return {
            "status": "success",
            "source_type": "historical",
            "days_covered": days,
            "stations_seeded": len(station_ids),
            "ingested_count": total_ingested,
            "duplicates_skipped": total_duplicates,
        }


historical_service = HistoricalDatasetService()
