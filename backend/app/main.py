from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.services.database import db_manager
from app.routes.health import router as health_router
from app.routes.locations import router as locations_router
from app.routes.readings import router as readings_router
from app.routes.alerts import router as alerts_router
from app.routes.analytics import router as analytics_router
from app.routes.seed import router as seed_router
from app.routes.ingestion import router as ingestion_router
from app.routes.forecast import router as forecast_router
from app.routes.auth import router as auth_router
from app.routes.reports import router as reports_router
from app.services.simulation_service import simulator


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager to connect/disconnect MongoDB Atlas and simulator."""
    # Connect to MongoDB Atlas (safe fallback if credentials pending)
    await db_manager.connect()
    
    # Optionally start simulator if auto-start configured
    if settings.SIMULATOR_AUTO_START:
        simulator.start()
        
    yield
    
    # Cleanly stop simulation background tasks
    simulator.stop()
    # Disconnect from MongoDB Atlas
    await db_manager.disconnect()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API and Telemetry Service for EcoPulse AI: Cloud-Based Environmental Monitoring, Analytics & Prediction Platform.",
    version="0.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Cross-Origin Resource Sharing (CORS) for frontend-backend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers under /api
app.include_router(health_router, prefix="/api")
app.include_router(locations_router, prefix="/api")
app.include_router(readings_router, prefix="/api")
app.include_router(alerts_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(seed_router, prefix="/api")
app.include_router(ingestion_router, prefix="/api")
app.include_router(forecast_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(reports_router, prefix="/api")

# Also alias /health at root for convenience
app.include_router(health_router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "platform": "EcoPulse AI",
        "service": "Cloud-Based Environmental Monitoring, Analytics & Prediction Platform",
        "version": "0.3.0",
        "documentation": "/docs",
        "endpoints": {
            "health": "/api/health",
            "locations": "/api/locations",
            "readings": "/api/readings",
            "readings_history": "/api/readings/history",
            "forecast_predict": "/api/forecast/predict",
            "forecast_model_status": "/api/forecast/model-status",
            "forecast_evaluation": "/api/forecast/evaluation",
            "forecast_train": "/api/forecast/train",
            "ingestion_status": "/api/ingestion/status",
            "ingestion_fetch_real": "/api/ingestion/fetch-real",
            "ingestion_simulate_status": "/api/ingestion/simulate/status",
            "alerts": "/api/alerts",
            "alerts_stats": "/api/alerts/stats",
            "alerts_thresholds": "/api/alerts/thresholds",
            "analytics_summary": "/api/analytics/summary",
            "reports_summary": "/api/reports/summary",
            "reports_csv": "/api/reports/readings/csv",
            "auth_register": "/api/auth/register",
            "auth_login": "/api/auth/login",
            "auth_me": "/api/auth/me",
            "seed": "/api/seed"
        },
        "database_status": db_manager.connection_status_message
    }
