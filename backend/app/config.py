import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "EcoPulse AI: Cloud-Based Environmental Monitoring, Analytics & Prediction Platform"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # Comma-separated list of allowed origins
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    
    # MongoDB Atlas Configuration (Credentials loaded from .env)
    MONGODB_URI: str = ""
    MONGODB_DB_NAME: str = "ecopulse_ai"
    MONGODB_TIMEOUT_MS: int = 2500

    # External Environmental & Weather API Configuration
    WEATHER_API_PROVIDER: str = "open-meteo"  # "open-meteo", "openweather", "waqi"
    OPEN_METEO_AIR_QUALITY_URL: str = "https://air-quality-api.open-meteo.com/v1"
    OPEN_METEO_WEATHER_URL: str = "https://api.open-meteo.com/v1"
    OPENWEATHER_API_KEY: str = ""
    WAQI_API_KEY: str = ""
    EXTERNAL_API_TIMEOUT_SECONDS: int = 10
    EXTERNAL_API_RATE_LIMIT_BACKOFF_SECONDS: int = 60
    
    # Telemetry Simulation Configuration
    SIMULATOR_UPDATE_INTERVAL_SECONDS: int = 15
    SIMULATOR_AUTO_START: bool = False
    
    # Ingestion & Deduplication Window
    DEDUPLICATION_WINDOW_SECONDS: int = 30

    # JWT Authentication Settings
    JWT_SECRET_KEY: str = "ecopulse-jwt-secret-key-change-in-production-2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 Hours

    # Environmental Incident Notification / SMTP Settings (Optional)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    ALERT_EMAIL_FROM: str = "alerts@ecopulse.ai"
    ALERT_NOTIFICATION_EMAIL: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        if not self.CORS_ORIGINS:
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
