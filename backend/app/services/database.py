import logging
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings
from app.services.seed_data import (
    SEED_LOCATIONS,
    SEED_READINGS,
    SEED_ALERTS,
    SEED_PREDICTIONS,
    SEED_USERS,
)

logger = logging.getLogger("ecopulse.database")


class DatabaseManager:
    """Manages asynchronous connections to MongoDB Atlas with in-memory fallback."""

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.is_connected: bool = False
        self.connection_status_message: str = "Initialized"
        
        # In-memory local stores for stage 1 local testing when Atlas is unconfigured
        self.memory_store: Dict[str, List[Dict[str, Any]]] = {
            "monitoring_locations": [dict(x) for x in SEED_LOCATIONS],
            "environmental_readings": [dict(x) for x in SEED_READINGS],
            "alerts": [dict(x) for x in SEED_ALERTS],
            "prediction_results": [dict(x) for x in SEED_PREDICTIONS],
            "users": [dict(x) for x in SEED_USERS],
            "thresholds": {
                "pm25": {"warning": 35.0, "critical": 75.0, "unit": "µg/m³", "comparison": "gt"},
                "pm10": {"warning": 50.0, "critical": 150.0, "unit": "µg/m³", "comparison": "gt"},
                "aqi": {"warning": 100.0, "critical": 200.0, "unit": "AQI Index", "comparison": "gt"},
                "co2": {"warning": 800.0, "critical": 1500.0, "unit": "ppm", "comparison": "gt"},
                "temperature": {"warning": 38.0, "critical": 45.0, "unit": "°C", "comparison": "gt"},
                "humidity": {"warning": 85.0, "critical": 95.0, "unit": "%", "comparison": "gt"},
            },
        }

    async def connect(self):
        """Attempts to establish connection to MongoDB Atlas."""
        uri = settings.MONGODB_URI.strip()
        
        # Check if URI is missing or using unreplaced placeholder
        if not uri or "<username>" in uri or "<password>" in uri:
            self.is_connected = False
            self.connection_status_message = (
                "MongoDB Atlas URI pending configuration in backend/.env. Running with local telemetry fallback."
            )
            logger.info(self.connection_status_message)
            return

        try:
            logger.info("Connecting to MongoDB Atlas cluster...")
            self.client = AsyncIOMotorClient(
                uri,
                serverSelectionTimeoutMS=settings.MONGODB_TIMEOUT_MS,
                connectTimeoutMS=settings.MONGODB_TIMEOUT_MS,
            )
            # Ping the admin database to verify cluster reachability
            await self.client.admin.command("ping")
            self.db = self.client[settings.MONGODB_DB_NAME]
            self.is_connected = True
            self.connection_status_message = f"Connected to MongoDB Atlas database: {settings.MONGODB_DB_NAME}"
            logger.info(self.connection_status_message)

            # Ensure optimal database indexes
            await self._create_indexes()

        except Exception as e:
            self.is_connected = False
            self.connection_status_message = f"Atlas connection failed: {str(e)[:120]}. Falling back to in-memory store."
            logger.warning(self.connection_status_message)

    async def _create_indexes(self):
        """Create indexes on MongoDB Atlas collections."""
        try:
            if self.db is not None:
                await self.db.environmental_readings.create_index([("location_id", 1), ("recorded_at", -1)])
                await self.db.monitoring_locations.create_index([("id", 1)], unique=True)
                await self.db.alerts.create_index([("location_id", 1), ("created_at", -1)])
                await self.db.users.create_index([("username", 1)], unique=True)
                logger.info("MongoDB Atlas indexes verified successfully.")
        except Exception as err:
            logger.warning(f"Index creation warning: {err}")

    async def disconnect(self):
        """Close MongoDB Atlas connection client."""
        if self.client:
            self.client.close()
            self.is_connected = False
            logger.info("MongoDB Atlas connection closed.")

    # -------------------------------------------------------------
    # Collection Accessors
    # -------------------------------------------------------------
    @property
    def users(self):
        return self.db.users if self.is_connected and self.db is not None else None

    @property
    def monitoring_locations(self):
        return self.db.monitoring_locations if self.is_connected and self.db is not None else None

    @property
    def environmental_readings(self):
        return self.db.environmental_readings if self.is_connected and self.db is not None else None

    @property
    def alerts(self):
        return self.db.alerts if self.is_connected and self.db is not None else None

    @property
    def prediction_results(self):
        return self.db.prediction_results if self.is_connected and self.db is not None else None

    @property
    def thresholds(self):
        return self.db.thresholds if self.is_connected and self.db is not None else None


db_manager = DatabaseManager()

