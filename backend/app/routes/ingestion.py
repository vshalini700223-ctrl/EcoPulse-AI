"""Data Ingestion & Telemetry Source Management Router for EcoPulse AI.

Provides endpoints for:
- Live environmental reading ingestion with normalization & deduplication
- Batch readings ingestion
- On-demand real data retrieval from external weather & air quality APIs
- Simulator control (start, stop, status)
- Ingestion telemetry status and external API availability & rate limit monitoring
- Historical telemetry dataset seeding
"""

import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, Body, HTTPException, status
from pydantic import BaseModel, Field

from app.models.reading import (
    ReadingCreate,
    ReadingResponse,
    IngestionResult,
    BatchIngestionResponse,
)
from app.models.common import generate_uuid, get_current_utc_iso
from app.services.database import db_manager
from app.services.normalization_service import normalizer
from app.services.real_data_service import (
    real_data_service,
    ExternalApiException,
    RateLimitExceededException,
)
from app.services.simulation_service import simulator
from app.services.historical_dataset import historical_service

logger = logging.getLogger("ecopulse.ingestion")

router = APIRouter(prefix="/ingestion", tags=["Data Ingestion & Telemetry Sources"])


class IngestSingleRequest(BaseModel):
    location_id: str = Field(..., description="Target station ID (e.g. station-alpha)")
    pm25: float = Field(..., ge=0.0, le=1000.0)
    pm10: float = Field(..., ge=0.0, le=2000.0)
    temperature: float = Field(..., ge=-60.0, le=70.0)
    humidity: float = Field(..., ge=0.0, le=100.0)
    aqi: Optional[int] = Field(default=None, ge=0, le=500)
    co2: Optional[float] = None
    no2: Optional[float] = None
    o3: Optional[float] = None
    co: Optional[float] = None
    so2: Optional[float] = None
    timestamp: Optional[str] = None
    source_type: str = Field(default="simulated", description="'real', 'simulated', or 'historical'")
    source_provider: Optional[str] = Field(default=None)


class FetchRealRequest(BaseModel):
    location_id: Optional[str] = Field(default=None, description="Optional single location ID; fetches all if null")


def resolve_station_name(location_id: str) -> str:
    """Find human-readable station name for a given location ID."""
    locations = db_manager.memory_store.get("monitoring_locations", [])
    for loc in locations:
        if loc.get("id") == location_id:
            return loc.get("name", location_id)
    return location_id


@router.post("/reading", response_model=IngestionResult, status_code=status.HTTP_201_CREATED, summary="Ingest Single Normalized Reading")
async def ingest_reading(payload: IngestSingleRequest):
    """Ingest a single environmental telemetry reading with validation, normalization,
    and deduplication protection.
    """
    raw_dict = payload.model_dump()
    raw_dict["recorded_at"] = payload.timestamp or get_current_utc_iso()

    # 1. Normalize reading
    normalized = normalizer.normalize_reading(
        raw=raw_dict,
        source_type=payload.source_type,
        source_provider=payload.source_provider or "api-ingest",
        retrieved_at=get_current_utc_iso(),
    )

    # 2. Check for duplicate ingestion
    is_dup, existing_id = await normalizer.is_duplicate(
        location_id=normalized["location_id"],
        recorded_at=normalized["recorded_at"],
        source_type=normalized["source_type"],
        dedup_hash=normalized["dedup_hash"],
    )

    if is_dup:
        logger.info(f"Duplicate reading detected for {normalized['location_id']} at {normalized['recorded_at']}. Ingestion skipped.")
        return {
            "status": "duplicate_skipped",
            "is_duplicate": True,
            "reading": None,
            "message": f"Duplicate telemetry detected (matching record ID {existing_id}). Ingestion rejected to prevent double-counting.",
        }

    reading_id = f"rdg-{generate_uuid()[:8]}"
    normalized["id"] = reading_id
    normalized["location_name"] = resolve_station_name(normalized["location_id"])

    # 3. Persist to MongoDB or in-memory store
    if db_manager.is_connected and db_manager.environmental_readings is not None:
        try:
            await db_manager.environmental_readings.insert_one(dict(normalized))
            if db_manager.monitoring_locations is not None:
                await db_manager.monitoring_locations.update_one(
                    {"id": normalized["location_id"]},
                    {
                        "$set": {
                            "current_aqi": normalized["aqi"],
                            "current_status": normalized["aqi_category"],
                            "updated_at": normalized["recorded_at"],
                        }
                    },
                )
        except Exception as err:
            logger.error(f"Error persisting ingested reading: {err}")
            raise HTTPException(status_code=500, detail=f"Database ingestion failure: {str(err)}")
    else:
        db_manager.memory_store["environmental_readings"].insert(0, normalized)
        for loc in db_manager.memory_store.get("monitoring_locations", []):
            if loc.get("id") == normalized["location_id"]:
                loc["current_aqi"] = normalized["aqi"]
                loc["current_status"] = normalized["aqi_category"]
                loc["updated_at"] = normalized["recorded_at"]

    return {
        "status": "success",
        "is_duplicate": False,
        "reading": normalized,
        "message": f"Reading successfully ingested and categorized as '{normalized['aqi_category']}'.",
    }


@router.post("/batch", response_model=BatchIngestionResponse, summary="Batch Ingest Environmental Readings")
async def ingest_batch(readings: List[IngestSingleRequest]):
    """Batch ingest telemetry records with individual normalization and deduplication filtering."""
    total = len(readings)
    ingested_count = 0
    duplicates_skipped = 0
    errors_count = 0
    details = []

    for item in readings:
        try:
            raw = item.model_dump()
            raw["recorded_at"] = item.timestamp or get_current_utc_iso()
            norm = normalizer.normalize_reading(
                raw=raw,
                source_type=item.source_type,
                source_provider=item.source_provider or "batch-ingest",
            )

            is_dup, _ = await normalizer.is_duplicate(
                location_id=norm["location_id"],
                recorded_at=norm["recorded_at"],
                source_type=norm["source_type"],
                dedup_hash=norm["dedup_hash"],
            )

            if is_dup:
                duplicates_skipped += 1
                continue

            reading_id = f"rdg-{generate_uuid()[:8]}"
            norm["id"] = reading_id
            norm["location_name"] = resolve_station_name(norm["location_id"])

            if db_manager.is_connected and db_manager.environmental_readings is not None:
                await db_manager.environmental_readings.insert_one(dict(norm))
            else:
                db_manager.memory_store["environmental_readings"].insert(0, norm)

            ingested_count += 1
        except Exception as err:
            errors_count += 1
            details.append(f"Failed to ingest reading for {item.location_id}: {str(err)}")

    return {
        "status": "completed",
        "total_submitted": total,
        "ingested_count": ingested_count,
        "duplicates_skipped": duplicates_skipped,
        "errors_count": errors_count,
        "details": details[:10],
    }


@router.post("/fetch-real", summary="Trigger Real Environmental Data Retrieval")
async def fetch_real_data(body: Optional[FetchRealRequest] = None):
    """Retrieve verified real environmental & weather telemetry from configured external APIs
    for specific or all registered monitoring locations.
    Strictly preserves source integrity: does NOT substitute simulated data if real API is unavailable.
    """
    target_loc_id = body.location_id if body else None

    # Load locations
    locations = []
    if db_manager.is_connected and db_manager.monitoring_locations is not None:
        try:
            q = {"id": target_loc_id} if target_loc_id else {}
            cursor = db_manager.monitoring_locations.find(q, {"_id": 0})
            locations = await cursor.to_list(length=100)
        except Exception as e:
            logger.warning(f"Error fetching locations for real API: {e}")

    if not locations:
        mem_locs = db_manager.memory_store.get("monitoring_locations", [])
        if target_loc_id:
            locations = [l for l in mem_locs if l.get("id") == target_loc_id]
        else:
            locations = mem_locs

    if not locations:
        raise HTTPException(status_code=404, detail="No registered monitoring locations found.")

    results = []
    failed_stations = []

    for loc in locations:
        loc_id = loc.get("id")
        lat = loc.get("latitude")
        lon = loc.get("longitude")

        if lat is None or lon is None:
            failed_stations.append({"location_id": loc_id, "error": "Station missing geographic coordinates."})
            continue

        try:
            # Query external API (strictly no simulated substitution)
            real_reading = await real_data_service.fetch_real_data_for_location(
                location_id=loc_id, latitude=lat, longitude=lon
            )

            # Prevent duplicate
            is_dup, _ = await normalizer.is_duplicate(
                location_id=loc_id,
                recorded_at=real_reading["recorded_at"],
                source_type="real",
                dedup_hash=real_reading.get("dedup_hash"),
            )

            if not is_dup:
                real_reading["id"] = f"real-{generate_uuid()[:8]}"
                real_reading["location_name"] = loc.get("name", loc_id)

                if db_manager.is_connected and db_manager.environmental_readings is not None:
                    await db_manager.environmental_readings.insert_one(dict(real_reading))
                    if db_manager.monitoring_locations is not None:
                        await db_manager.monitoring_locations.update_one(
                            {"id": loc_id},
                            {
                                "$set": {
                                    "current_aqi": real_reading["aqi"],
                                    "current_status": real_reading["aqi_category"],
                                    "updated_at": real_reading["recorded_at"],
                                }
                            },
                        )
                else:
                    db_manager.memory_store["environmental_readings"].insert(0, real_reading)
                    loc["current_aqi"] = real_reading["aqi"]
                    loc["current_status"] = real_reading["aqi_category"]
                    loc["updated_at"] = real_reading["recorded_at"]

            results.append({
                "location_id": loc_id,
                "location_name": loc.get("name", loc_id),
                "status": "retrieved",
                "is_duplicate": is_dup,
                "data": real_reading,
            })

        except RateLimitExceededException as rle:
            failed_stations.append({
                "location_id": loc_id,
                "status": "rate_limited",
                "error": str(rle),
            })
        except ExternalApiException as eae:
            failed_stations.append({
                "location_id": loc_id,
                "status": "api_unavailable",
                "error": str(eae),
            })
        except Exception as err:
            failed_stations.append({
                "location_id": loc_id,
                "status": "error",
                "error": f"Unexpected error during real data query: {str(err)}",
            })

    api_health = real_data_service.get_api_status()

    return {
        "status": "completed" if not failed_stations else "partial" if results else "failed",
        "provider": api_health["provider"],
        "api_availability": api_health["status"],
        "total_attempted": len(locations),
        "successful_count": len(results),
        "failed_count": len(failed_stations),
        "retrieved_readings": results,
        "failures": failed_stations,
    }


@router.post("/simulate/start", summary="Start Environmental Telemetry Simulator")
async def start_simulator(
    interval: Optional[int] = Query(None, ge=2, le=300, description="Update interval in seconds (default 15s)"),
):
    """Start asynchronous background environmental telemetry generation with configurable interval."""
    res = simulator.start(interval_seconds=interval)
    return res


@router.post("/simulate/stop", summary="Stop Environmental Telemetry Simulator")
async def stop_simulator():
    """Safely terminate the background telemetry simulation engine."""
    res = simulator.stop()
    return res


@router.get("/simulate/status", summary="Get Simulator Operational Status")
async def get_simulator_status():
    """Query current status, emission rate, and record counter of the simulation engine."""
    return simulator.get_status()


@router.get("/status", summary="Query Telemetry Sources & External API Availability")
async def get_ingestion_status():
    """Diagnostic endpoint reporting external weather/air API availability, rate limits,
    failure history, and active simulation status.
    """
    api_diag = real_data_service.get_api_status()
    sim_diag = simulator.get_status()

    # Query collection counts by source_type
    counts = {"real": 0, "simulated": 0, "historical": 0, "total": 0}
    if db_manager.is_connected and db_manager.environmental_readings is not None:
        try:
            counts["total"] = await db_manager.environmental_readings.count_documents({})
            counts["real"] = await db_manager.environmental_readings.count_documents({"source_type": "real"})
            counts["simulated"] = await db_manager.environmental_readings.count_documents({"source_type": "simulated"})
            counts["historical"] = await db_manager.environmental_readings.count_documents({"source_type": "historical"})
        except Exception:
            pass
    else:
        readings = db_manager.memory_store.get("environmental_readings", [])
        counts["total"] = len(readings)
        for r in readings:
            st = r.get("source_type", "simulated")
            if st in counts:
                counts[st] += 1

    return {
        "external_api": api_diag,
        "simulator": sim_diag,
        "records_by_source": counts,
        "timestamp": get_current_utc_iso(),
    }


@router.post("/historical/seed", summary="Seed Multi-Day Historical Telemetry Dataset")
async def seed_historical_telemetry(days: int = Query(7, ge=1, le=30, description="Days of historical hourly data to generate")):
    """Seed authentic multi-day historical environmental readings for ML training and analytics."""
    res = await historical_service.seed_historical_data(days=days)
    return res
