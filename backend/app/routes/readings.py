import math
from typing import Optional
from fastapi import APIRouter, Query, status, HTTPException
from app.models.reading import (
    ReadingCreate,
    ReadingResponse,
    PaginatedReadingsResponse,
    HistoricalSummaryResponse,
)
from app.models.common import generate_uuid, get_current_utc_iso
from app.services.database import db_manager
from app.services.normalization_service import normalizer

router = APIRouter(prefix="/readings", tags=["Environmental Readings"])


def resolve_station_name(location_id: str) -> str:
    """Find human-readable station name for a given location ID."""
    locations = db_manager.memory_store.get("monitoring_locations", [])
    for loc in locations:
        if loc.get("id") == location_id:
            return loc.get("name", location_id)
    return location_id


@router.get("", response_model=PaginatedReadingsResponse, summary="Query Historical Telemetry Readings")
async def get_readings(
    location_id: Optional[str] = Query(None, description="Filter by location ID (e.g. station-alpha)"),
    source_type: Optional[str] = Query(None, description="Filter by data origin: 'real', 'simulated', or 'historical'"),
    start_date: Optional[str] = Query(None, description="Start date ISO string (e.g. 2026-10-01T00:00:00Z)"),
    end_date: Optional[str] = Query(None, description="End date ISO string"),
    page: int = Query(1, ge=1, description="Page index (1-based)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """Retrieve paginated environmental telemetry readings with location, source_type, and date range filters."""
    query = {}
    if location_id:
        query["location_id"] = location_id
    if source_type:
        query["source_type"] = source_type

    # Date range filters on recorded_at
    date_filter = {}
    if start_date:
        date_filter["$gte"] = start_date
    if end_date:
        date_filter["$lte"] = end_date
    if date_filter:
        query["recorded_at"] = date_filter

    if db_manager.is_connected and db_manager.environmental_readings is not None:
        total = await db_manager.environmental_readings.count_documents(query)
        skip = (page - 1) * limit
        cursor = (
            db_manager.environmental_readings.find(query, {"_id": 0})
            .sort("recorded_at", -1)
            .skip(skip)
            .limit(limit)
        )
        items = await cursor.to_list(length=limit)
        total_pages = math.ceil(total / limit) if total > 0 else 1
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "items": items,
        }

    # In-memory fallback
    all_readings = db_manager.memory_store.get("environmental_readings", [])
    filtered = []
    for r in all_readings:
        if location_id and r.get("location_id") != location_id:
            continue
        if source_type and r.get("source_type") != source_type:
            continue
        rec_time = r.get("recorded_at", "")
        if start_date and rec_time < start_date:
            continue
        if end_date and rec_time > end_date:
            continue
        filtered.append(r)

    # Sort descending by recorded_at
    filtered.sort(key=lambda x: x.get("recorded_at", ""), reverse=True)
    total = len(filtered)
    skip = (page - 1) * limit
    items = filtered[skip : skip + limit]
    total_pages = math.ceil(total / limit) if total > 0 else 1

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "items": items,
    }


@router.get("/history", response_model=HistoricalSummaryResponse, summary="Query Historical Telemetry Analytics")
async def get_historical_readings(
    location_id: Optional[str] = Query(None, description="Station ID filter"),
    source_type: Optional[str] = Query(None, description="Filter by 'real', 'simulated', or 'historical'"),
    start_date: Optional[str] = Query(None, description="Start date ISO string"),
    end_date: Optional[str] = Query(None, description="End date ISO string"),
    limit: int = Query(100, ge=1, le=1000, description="Max readings to return"),
):
    """Query environmental time-series history with aggregated metrics (average AQI, min/max bounds, PM levels)."""
    query = {}
    if location_id:
        query["location_id"] = location_id
    if source_type:
        query["source_type"] = source_type

    date_filter = {}
    if start_date:
        date_filter["$gte"] = start_date
    if end_date:
        date_filter["$lte"] = end_date
    if date_filter:
        query["recorded_at"] = date_filter

    readings = []
    if db_manager.is_connected and db_manager.environmental_readings is not None:
        cursor = (
            db_manager.environmental_readings.find(query, {"_id": 0})
            .sort("recorded_at", -1)
            .limit(limit)
        )
        readings = await cursor.to_list(length=limit)
    else:
        all_r = db_manager.memory_store.get("environmental_readings", [])
        for r in all_r:
            if location_id and r.get("location_id") != location_id:
                continue
            if source_type and r.get("source_type") != source_type:
                continue
            t = r.get("recorded_at", "")
            if start_date and t < start_date:
                continue
            if end_date and t > end_date:
                continue
            readings.append(r)
        readings.sort(key=lambda x: x.get("recorded_at", ""), reverse=True)
        readings = readings[:limit]

    # Calculate summary aggregations
    if readings:
        aqis = [r.get("aqi") for r in readings if r.get("aqi") is not None]
        pm25s = [r.get("pm25") for r in readings if r.get("pm25") is not None]
        pm10s = [r.get("pm10") for r in readings if r.get("pm10") is not None]
        temps = [r.get("temperature") for r in readings if r.get("temperature") is not None]
        hums = [r.get("humidity") for r in readings if r.get("humidity") is not None]

        avg_aqi = round(sum(aqis) / len(aqis), 1) if aqis else None
        min_aqi = min(aqis) if aqis else None
        max_aqi = max(aqis) if aqis else None
        avg_pm25 = round(sum(pm25s) / len(pm25s), 1) if pm25s else None
        avg_pm10 = round(sum(pm10s) / len(pm10s), 1) if pm10s else None
        avg_temp = round(sum(temps) / len(temps), 1) if temps else None
        avg_hum = round(sum(hums) / len(hums), 1) if hums else None
    else:
        avg_aqi = min_aqi = max_aqi = avg_pm25 = avg_pm10 = avg_temp = avg_hum = None

    return {
        "location_id": location_id,
        "source_type": source_type,
        "total_records": len(readings),
        "average_aqi": avg_aqi,
        "min_aqi": min_aqi,
        "max_aqi": max_aqi,
        "average_pm25": avg_pm25,
        "average_pm10": avg_pm10,
        "average_temperature": avg_temp,
        "average_humidity": avg_hum,
        "items": readings,
    }


@router.post("", response_model=ReadingResponse, status_code=status.HTTP_201_CREATED, summary="Ingest Environmental Reading")
async def create_reading(reading_in: ReadingCreate):
    """Ingest real-time environmental telemetry from a monitoring station node."""
    reading_id = f"rdg-{generate_uuid()[:8]}"
    recorded_at = reading_in.timestamp or get_current_utc_iso()
    loc_name = resolve_station_name(reading_in.location_id)
    source_type = reading_in.source_type or "simulated"
    source_provider = reading_in.source_provider or "direct-ingest"

    # Normalize reading
    normalized = normalizer.normalize_reading(
        raw={
            "location_id": reading_in.location_id,
            "pm25": reading_in.pm25,
            "pm10": reading_in.pm10,
            "aqi": reading_in.aqi,
            "aqi_category": reading_in.aqi_category,
            "temperature": reading_in.temperature,
            "humidity": reading_in.humidity,
            "co2": reading_in.co2,
            "no2": reading_in.no2,
            "o3": reading_in.o3,
            "co": reading_in.co,
            "so2": reading_in.so2,
            "recorded_at": recorded_at,
        },
        source_type=source_type,
        source_provider=source_provider,
        retrieved_at=reading_in.retrieved_at or get_current_utc_iso(),
    )

    # Check for duplicate
    is_dup, _ = await normalizer.is_duplicate(
        location_id=normalized["location_id"],
        recorded_at=normalized["recorded_at"],
        source_type=source_type,
        dedup_hash=normalized.get("dedup_hash"),
    )

    new_reading = {
        "id": reading_id,
        "location_id": normalized["location_id"],
        "location_name": loc_name,
        "pm25": normalized["pm25"],
        "pm10": normalized["pm10"],
        "aqi": normalized["aqi"],
        "aqi_category": normalized["aqi_category"],
        "temperature": normalized["temperature"],
        "humidity": normalized["humidity"],
        "co2": normalized["co2"],
        "no2": normalized["no2"],
        "o3": normalized["o3"],
        "co": normalized["co"],
        "so2": normalized["so2"],
        "source_type": source_type,
        "source_provider": source_provider,
        "retrieved_at": normalized.get("retrieved_at"),
        "dedup_hash": normalized.get("dedup_hash"),
        "recorded_at": normalized["recorded_at"],
        "is_duplicate": is_dup,
    }

    if not is_dup:
        if db_manager.is_connected and db_manager.environmental_readings is not None:
            try:
                await db_manager.environmental_readings.insert_one(dict(new_reading))
                # Also update latest reading on the location doc
                if db_manager.monitoring_locations is not None:
                    await db_manager.monitoring_locations.update_one(
                        {"id": reading_in.location_id},
                        {
                            "$set": {
                                "current_aqi": normalized["aqi"],
                                "current_status": normalized["aqi_category"],
                                "updated_at": normalized["recorded_at"],
                            }
                        },
                    )
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Database error during reading ingestion: {str(e)}")
        else:
            db_manager.memory_store["environmental_readings"].insert(0, new_reading)
            # Update in-memory location
            for loc in db_manager.memory_store.get("monitoring_locations", []):
                if loc.get("id") == reading_in.location_id:
                    loc["current_aqi"] = normalized["aqi"]
                    loc["current_status"] = normalized["aqi_category"]
                    loc["updated_at"] = normalized["recorded_at"]

    return new_reading
