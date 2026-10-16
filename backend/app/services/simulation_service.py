"""Environmental Telemetry Simulation Engine for EcoPulse AI.

Generates realistic continuous sensor readings (temperature, humidity, PM2.5, PM10,
CO2, trace gases) for testing, staging, and locations without physical ground sensors.
Supports configurable intervals, station profiles, diurnal variation, and safe start/stop.
Every generated record is strictly marked with source_type = 'simulated'.
"""

import math
import random
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.config import settings
from app.models.common import generate_uuid, get_current_utc_iso
from app.services.database import db_manager
from app.services.normalization_service import normalizer

logger = logging.getLogger("ecopulse.simulator")

# Realistic environmental parameter baselines per ecosystem profile
STATION_PROFILES: Dict[str, Dict[str, Any]] = {
    "station-alpha": {
        "ecosystem": "Forest & Watershed",
        "pm25_base": 10.5,
        "pm25_variance": 4.0,
        "pm10_base": 20.0,
        "pm10_variance": 7.0,
        "temp_base": 22.0,
        "temp_variance": 3.0,
        "humidity_base": 78.0,
        "humidity_variance": 8.0,
        "co2_base": 402.0,
    },
    "station-beta": {
        "ecosystem": "Urban Canyon",
        "pm25_base": 34.0,
        "pm25_variance": 12.0,
        "pm10_base": 68.0,
        "pm10_variance": 18.0,
        "temp_base": 27.5,
        "temp_variance": 3.5,
        "humidity_base": 55.0,
        "humidity_variance": 9.0,
        "co2_base": 455.0,
    },
    "station-gamma": {
        "ecosystem": "Heavy Industrial",
        "pm25_base": 56.0,
        "pm25_variance": 18.0,
        "pm10_base": 110.0,
        "pm10_variance": 28.0,
        "temp_base": 29.5,
        "temp_variance": 4.0,
        "humidity_base": 46.0,
        "humidity_variance": 8.0,
        "co2_base": 525.0,
    },
    "station-delta": {
        "ecosystem": "Wetland & Coast",
        "pm25_base": 13.0,
        "pm25_variance": 5.0,
        "pm10_base": 26.0,
        "pm10_variance": 9.0,
        "temp_base": 24.5,
        "temp_variance": 2.5,
        "humidity_base": 82.0,
        "humidity_variance": 7.0,
        "co2_base": 408.0,
    },
    "station-epsilon": {
        "ecosystem": "Suburban Tech Plateau",
        "pm25_base": 24.0,
        "pm25_variance": 8.0,
        "pm10_base": 48.0,
        "pm10_variance": 12.0,
        "temp_base": 25.0,
        "temp_variance": 3.0,
        "humidity_base": 60.0,
        "humidity_variance": 9.0,
        "co2_base": 428.0,
    },
}

DEFAULT_PROFILE: Dict[str, Any] = {
    "ecosystem": "Standard Monitoring Station",
    "pm25_base": 25.0,
    "pm25_variance": 8.0,
    "pm10_base": 50.0,
    "pm10_variance": 15.0,
    "temp_base": 25.0,
    "temp_variance": 3.0,
    "humidity_base": 60.0,
    "humidity_variance": 10.0,
    "co2_base": 420.0,
}


class SimulationService:
    """Manages asynchronous realistic environmental telemetry generation."""

    def __init__(self):
        self.interval_seconds: int = settings.SIMULATOR_UPDATE_INTERVAL_SECONDS
        self.is_running: bool = False
        self._task: Optional[asyncio.Task] = None
        self.started_at: Optional[str] = None
        self.stopped_at: Optional[str] = None
        self.records_generated: int = 0
        self.batches_emitted: int = 0
        self.last_emitted_at: Optional[str] = None

    def generate_single_reading(self, location_id: str, timestamp: Optional[str] = None) -> Dict[str, Any]:
        """Generate a physically plausible multi-sensor environmental reading."""
        profile = STATION_PROFILES.get(location_id, DEFAULT_PROFILE)
        rec_time = timestamp or get_current_utc_iso()

        # Diurnal solar cycle calculation (0 to 23 hours)
        try:
            dt = datetime.fromisoformat(rec_time.replace("Z", "+00:00"))
            hour = dt.hour + (dt.minute / 60.0)
        except Exception:
            hour = 12.0

        # Solar thermal curve: peaks around 14:00 (hour 14), lowest around 05:00
        solar_factor = math.sin((hour - 8.0) * math.pi / 12.0)

        # Temperature fluctuates with solar cycle
        temp = profile["temp_base"] + (solar_factor * profile["temp_variance"]) + random.uniform(-0.8, 0.8)
        temp = round(max(-20.0, min(55.0, temp)), 1)

        # Humidity is generally inverse to temperature
        humidity = profile["humidity_base"] - (solar_factor * (profile["humidity_variance"] * 0.7)) + random.uniform(-2.5, 2.5)
        humidity = round(max(10.0, min(98.0, humidity)), 1)

        # Particulate matter peaks during commuter rush hours (08:00 - 10:00 and 18:00 - 20:00)
        rush_hour_boost = 0.0
        if 7.5 <= hour <= 10.0 or 17.5 <= hour <= 20.5:
            rush_hour_boost = random.uniform(5.0, 18.0)

        pm25 = max(2.0, profile["pm25_base"] + rush_hour_boost + random.gauss(0, profile["pm25_variance"] * 0.35))
        pm10 = max(pm25 * 1.4, profile["pm10_base"] + (rush_hour_boost * 1.8) + random.gauss(0, profile["pm10_variance"] * 0.35))
        pm25 = round(pm25, 1)
        pm10 = round(pm10, 1)

        # CO2 and trace gases
        co2 = round(profile["co2_base"] + (rush_hour_boost * 2.2) + random.uniform(-8.0, 12.0), 1)
        no2 = round(max(5.0, 18.0 + (rush_hour_boost * 0.8) + random.uniform(-3.0, 5.0)), 1)
        o3 = round(max(5.0, 25.0 + (solar_factor * 15.0) + random.uniform(-4.0, 4.0)), 1)
        co = round(max(0.1, 0.4 + (rush_hour_boost * 0.03) + random.uniform(-0.05, 0.05)), 2)
        so2 = round(max(1.0, 8.0 + random.uniform(-2.0, 3.0)), 1)

        raw = {
            "location_id": location_id,
            "pm25": pm25,
            "pm10": pm10,
            "temperature": temp,
            "humidity": humidity,
            "co2": co2,
            "no2": no2,
            "o3": o3,
            "co": co,
            "so2": so2,
            "recorded_at": rec_time,
        }

        # Normalize with strict source tagging: source_type="simulated"
        normalized = normalizer.normalize_reading(
            raw=raw,
            source_type="simulated",
            source_provider="ecopulse-simulator",
            retrieved_at=rec_time,
        )
        return normalized

    async def ingest_simulated_cycle(self) -> int:
        """Run one generation cycle across all registered stations and ingest readings."""
        # Get active location IDs
        location_ids = []
        if db_manager.is_connected and db_manager.monitoring_locations is not None:
            try:
                cursor = db_manager.monitoring_locations.find({}, {"id": 1, "_id": 0})
                locs = await cursor.to_list(length=100)
                location_ids = [l["id"] for l in locs if "id" in l]
            except Exception as e:
                logger.warning(f"Error fetching locations for simulation: {e}")

        if not location_ids:
            location_ids = [l["id"] for l in db_manager.memory_store.get("monitoring_locations", [])]
        if not location_ids:
            location_ids = list(STATION_PROFILES.keys())

        ingested_count = 0
        now_iso = get_current_utc_iso()

        for loc_id in location_ids:
            reading_dict = self.generate_single_reading(loc_id, timestamp=now_iso)
            reading_id = f"sim-{generate_uuid()[:8]}"
            reading_dict["id"] = reading_id

            # Save to Database or Memory Store
            if db_manager.is_connected and db_manager.environmental_readings is not None:
                try:
                    await db_manager.environmental_readings.insert_one(dict(reading_dict))
                    if db_manager.monitoring_locations is not None:
                        await db_manager.monitoring_locations.update_one(
                            {"id": loc_id},
                            {
                                "$set": {
                                    "current_aqi": reading_dict["aqi"],
                                    "current_status": reading_dict["aqi_category"],
                                    "updated_at": now_iso,
                                }
                            },
                        )
                    ingested_count += 1
                except Exception as err:
                    logger.error(f"Failed to persist simulated reading to MongoDB: {err}")
            else:
                db_manager.memory_store["environmental_readings"].insert(0, reading_dict)
                # Keep memory store bounded (latest 200 items)
                if len(db_manager.memory_store["environmental_readings"]) > 200:
                    db_manager.memory_store["environmental_readings"] = db_manager.memory_store["environmental_readings"][:200]
                
                # Update location doc
                for loc in db_manager.memory_store.get("monitoring_locations", []):
                    if loc.get("id") == loc_id:
                        loc["current_aqi"] = reading_dict["aqi"]
                        loc["current_status"] = reading_dict["aqi_category"]
                        loc["updated_at"] = now_iso
                ingested_count += 1

        self.records_generated += ingested_count
        self.batches_emitted += 1
        self.last_emitted_at = now_iso
        return ingested_count

    async def _simulation_loop(self):
        """Asynchronous background loop for scheduled telemetry generation."""
        logger.info(f"EcoPulse Simulator started with interval {self.interval_seconds}s.")
        try:
            while self.is_running:
                try:
                    count = await self.ingest_simulated_cycle()
                    logger.debug(f"Simulator emitted {count} readings at {self.last_emitted_at}")
                except Exception as loop_err:
                    logger.error(f"Error during simulation cycle: {loop_err}")
                await asyncio.sleep(self.interval_seconds)
        except asyncio.CancelledError:
            logger.info("Simulator background loop safely cancelled.")
        finally:
            self.is_running = False

    def start(self, interval_seconds: Optional[int] = None) -> Dict[str, Any]:
        """Safely start the telemetry simulation task."""
        if interval_seconds and interval_seconds >= 2:
            self.interval_seconds = interval_seconds

        if self.is_running and self._task and not self._task.done():
            return {
                "status": "already_running",
                "message": f"Simulator is already active with interval {self.interval_seconds}s",
                "interval_seconds": self.interval_seconds,
                "records_generated": self.records_generated,
            }

        self.is_running = True
        self.started_at = get_current_utc_iso()
        self.stopped_at = None
        self._task = asyncio.create_task(self._simulation_loop())

        return {
            "status": "started",
            "message": f"Simulator started successfully with {self.interval_seconds}s update frequency",
            "interval_seconds": self.interval_seconds,
            "started_at": self.started_at,
        }

    def stop(self) -> Dict[str, Any]:
        """Safely stop the telemetry simulation task."""
        if not self.is_running and (self._task is None or self._task.done()):
            return {
                "status": "not_running",
                "message": "Simulator is not currently running",
                "records_generated": self.records_generated,
            }

        self.is_running = False
        self.stopped_at = get_current_utc_iso()
        if self._task and not self._task.done():
            self._task.cancel()

        return {
            "status": "stopped",
            "message": "Simulator background process stopped safely",
            "stopped_at": self.stopped_at,
            "records_generated": self.records_generated,
        }

    def get_status(self) -> Dict[str, Any]:
        """Return diagnostic state of the simulation engine."""
        return {
            "is_running": self.is_running,
            "interval_seconds": self.interval_seconds,
            "started_at": self.started_at,
            "stopped_at": self.stopped_at,
            "records_generated": self.records_generated,
            "batches_emitted": self.batches_emitted,
            "last_emitted_at": self.last_emitted_at,
            "active_profiles": list(STATION_PROFILES.keys()),
        }


simulator = SimulationService()
