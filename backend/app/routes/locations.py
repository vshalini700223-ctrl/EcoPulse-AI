from typing import List, Optional
from fastapi import APIRouter, Query, status, HTTPException
from app.models.location import LocationCreate, LocationResponse
from app.models.common import generate_uuid, get_current_utc_iso
from app.services.database import db_manager

router = APIRouter(prefix="/locations", tags=["Monitoring Locations"])


@router.get("", response_model=List[LocationResponse], summary="List Environmental Monitoring Locations")
async def get_locations(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (e.g. Active, Maintenance)")
):
    """Retrieve all configured environmental monitoring stations."""
    query = {}
    if status_filter:
        query["status"] = status_filter

    if db_manager.is_connected and db_manager.monitoring_locations is not None:
        cursor = db_manager.monitoring_locations.find(query, {"_id": 0})
        locations = await cursor.to_list(length=100)
        return locations

    # Local fallback store
    items = db_manager.memory_store.get("monitoring_locations", [])
    if status_filter:
        items = [x for x in items if x.get("status", "").lower() == status_filter.lower()]
    return items


@router.post("", response_model=LocationResponse, status_code=status.HTTP_201_CREATED, summary="Register New Monitoring Location")
async def create_location(location_in: LocationCreate):
    """Register a new ground sensor telemetry location node."""
    loc_id = f"loc-{generate_uuid()[:8]}"
    now = get_current_utc_iso()

    new_location = {
        "id": loc_id,
        "name": location_in.name,
        "zone": location_in.zone,
        "location_type": location_in.location_type,
        "latitude": location_in.latitude,
        "longitude": location_in.longitude,
        "status": location_in.status,
        "active_sensors": location_in.active_sensors,
        "total_sensors": location_in.total_sensors,
        "created_at": now,
        "updated_at": now,
        "current_aqi": 50,
        "current_status": "Good"
    }

    if db_manager.is_connected and db_manager.monitoring_locations is not None:
        try:
            await db_manager.monitoring_locations.insert_one(dict(new_location))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database insert error: {str(e)}")
    else:
        db_manager.memory_store["monitoring_locations"].append(new_location)

    return new_location
