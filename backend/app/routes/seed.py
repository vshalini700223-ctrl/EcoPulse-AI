from fastapi import APIRouter, status
from app.services.database import db_manager
from app.services.seed_data import (
    SEED_LOCATIONS,
    SEED_READINGS,
    SEED_ALERTS,
    SEED_PREDICTIONS,
    SEED_USERS,
)

router = APIRouter(prefix="/seed", tags=["Database Seeding"])


@router.post("", status_code=status.HTTP_201_CREATED, summary="Seed Database with Sample Telemetry")
async def seed_database():
    """Populates MongoDB Atlas (or in-memory store) with initial realistic environmental monitoring telemetry."""
    if db_manager.is_connected and db_manager.db is not None:
        # Clear existing collection data for clean re-seed
        await db_manager.db.monitoring_locations.delete_many({})
        await db_manager.db.environmental_readings.delete_many({})
        await db_manager.db.alerts.delete_many({})
        await db_manager.db.prediction_results.delete_many({})
        await db_manager.db.users.delete_many({})

        # Insert fresh seed documents
        loc_res = await db_manager.db.monitoring_locations.insert_many([dict(x) for x in SEED_LOCATIONS])
        rdg_res = await db_manager.db.environmental_readings.insert_many([dict(x) for x in SEED_READINGS])
        alt_res = await db_manager.db.alerts.insert_many([dict(x) for x in SEED_ALERTS])
        prd_res = await db_manager.db.prediction_results.insert_many([dict(x) for x in SEED_PREDICTIONS])
        usr_res = await db_manager.db.users.insert_many([dict(x) for x in SEED_USERS])

        return {
            "status": "success",
            "target": "MongoDB Atlas Cluster",
            "database": db_manager.db.name,
            "seeded": {
                "monitoring_locations": len(loc_res.inserted_ids),
                "environmental_readings": len(rdg_res.inserted_ids),
                "alerts": len(alt_res.inserted_ids),
                "prediction_results": len(prd_res.inserted_ids),
                "users": len(usr_res.inserted_ids),
            },
        }

    # In-memory store refresh
    db_manager.memory_store = {
        "monitoring_locations": [dict(x) for x in SEED_LOCATIONS],
        "environmental_readings": [dict(x) for x in SEED_READINGS],
        "alerts": [dict(x) for x in SEED_ALERTS],
        "prediction_results": [dict(x) for x in SEED_PREDICTIONS],
        "users": [dict(x) for x in SEED_USERS],
    }

    return {
        "status": "success",
        "target": "Local In-Memory Telemetry Store",
        "seeded": {
            "monitoring_locations": len(SEED_LOCATIONS),
            "environmental_readings": len(SEED_READINGS),
            "alerts": len(SEED_ALERTS),
            "prediction_results": len(SEED_PREDICTIONS),
            "users": len(SEED_USERS),
        },
    }
