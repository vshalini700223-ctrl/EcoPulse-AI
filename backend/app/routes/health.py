from datetime import datetime, timezone
from fastapi import APIRouter
from app.config import settings
from app.services.database import db_manager

router = APIRouter(tags=["System Health"])


@router.get("/health", summary="System Health & Database Telemetry Check")
async def health_check():
    """Returns the operational status of the EcoPulse AI backend and MongoDB Atlas integration."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.ENVIRONMENT,
        "version": "0.2.0-atlas-integrated",
        "database": {
            "connected": db_manager.is_connected,
            "status": db_manager.connection_status_message,
            "database_name": settings.MONGODB_DB_NAME,
            "collections": [
                "users",
                "monitoring_locations",
                "environmental_readings",
                "alerts",
                "prediction_results",
            ],
            "mode": "MongoDB Atlas Cluster" if db_manager.is_connected else "Local In-Memory Telemetry Fallback",
        },
        "cors_origins": settings.cors_origins_list,
    }
