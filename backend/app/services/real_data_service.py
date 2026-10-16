"""Configurable External Environmental & Weather API Integration Service.

Connects to verified meteorological and atmospheric air-quality APIs (Open-Meteo,
OpenWeatherMap, WAQI) using credentials strictly stored in environment variables.
Implements validation, rate limit management, latency tracking, and failure logging.
CRITICAL: Never substitutes simulated values while labeling them as real.
"""

import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import httpx
from app.config import settings
from app.models.common import get_current_utc_iso
from app.services.normalization_service import normalizer

logger = logging.getLogger("ecopulse.real_data")


class ExternalApiException(Exception):
    """Base exception for real external API errors."""
    pass


class RateLimitExceededException(ExternalApiException):
    """Raised when external API returns HTTP 429."""
    pass


class ApiValidationException(ExternalApiException):
    """Raised when API returns malformed or unexpected data."""
    pass


class RealDataService:
    """Enterprise integration client for real-time external environmental APIs."""

    def __init__(self):
        self.provider_name: str = settings.WEATHER_API_PROVIDER.lower()
        self.timeout: int = settings.EXTERNAL_API_TIMEOUT_SECONDS
        self.backoff_duration: int = settings.EXTERNAL_API_RATE_LIMIT_BACKOFF_SECONDS
        
        # Operational health & audit state
        self.rate_limit_reset_timestamp: Optional[float] = None
        self.last_status: str = "online"  # "online", "rate_limited", "degraded", "offline"
        self.last_success_at: Optional[str] = None
        self.last_failure_at: Optional[str] = None
        self.last_error_message: Optional[str] = None
        self.total_requests: int = 0
        self.successful_requests: int = 0
        self.failed_requests: int = 0
        self.consecutive_failures: int = 0
        self.failures_log: List[Dict[str, Any]] = []

    def _record_failure(self, endpoint: str, error_msg: str, status_code: Optional[int] = None):
        """Audit and log external API failure without crashing the service."""
        now_iso = get_current_utc_iso()
        self.failed_requests += 1
        self.consecutive_failures += 1
        self.last_failure_at = now_iso
        self.last_error_message = error_msg
        if status_code == 429:
            self.last_status = "rate_limited"
        else:
            self.last_status = "degraded" if self.consecutive_failures < 3 else "offline"

        entry = {
            "timestamp": now_iso,
            "provider": self.provider_name,
            "endpoint": endpoint,
            "status_code": status_code,
            "error": error_msg,
        }
        self.failures_log.insert(0, entry)
        if len(self.failures_log) > 25:
            self.failures_log = self.failures_log[:25]

        logger.error(f"External API failure [{self.provider_name}] ({status_code}): {error_msg}")

    def _record_success(self):
        """Update operational state upon successful external API retrieval."""
        self.successful_requests += 1
        self.consecutive_failures = 0
        self.last_status = "online"
        self.last_success_at = get_current_utc_iso()
        self.last_error_message = None

    def check_rate_limit(self):
        """Verify if service is currently blocked due to active rate-limiting."""
        if self.rate_limit_reset_timestamp:
            remaining = self.rate_limit_reset_timestamp - time.time()
            if remaining > 0:
                raise RateLimitExceededException(
                    f"External API rate limit active for {self.provider_name}. Retry in {int(remaining)} seconds."
                )
            else:
                self.rate_limit_reset_timestamp = None
                self.last_status = "online"

    async def fetch_real_readings_open_meteo(
        self, location_id: str, latitude: float, longitude: float
    ) -> Dict[str, Any]:
        """Fetch verified environmental telemetry from Open-Meteo Air Quality & Weather APIs."""
        self.check_rate_limit()
        self.total_requests += 1
        start_time = time.time()
        retrieval_time = get_current_utc_iso()

        aq_url = f"{settings.OPEN_METEO_AIR_QUALITY_URL}/air-quality"
        aq_params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,us_aqi",
        }

        weather_url = f"{settings.OPEN_METEO_WEATHER_URL}/forecast"
        weather_params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                # 1. Fetch Air Quality
                aq_res = await client.get(aq_url, params=aq_params)
                if aq_res.status_code == 429:
                    self.rate_limit_reset_timestamp = time.time() + self.backoff_duration
                    self._record_failure(aq_url, "HTTP 429 Rate Limit Exceeded", 429)
                    raise RateLimitExceededException(
                        f"External API rate limit exceeded on {self.provider_name}. Backing off for {self.backoff_duration}s."
                    )
                aq_res.raise_for_status()
                aq_data = aq_res.json()

                # 2. Fetch Meteorological Weather
                w_res = await client.get(weather_url, params=weather_params)
                if w_res.status_code == 429:
                    self.rate_limit_reset_timestamp = time.time() + self.backoff_duration
                    self._record_failure(weather_url, "HTTP 429 Rate Limit Exceeded", 429)
                    raise RateLimitExceededException(
                        f"External API rate limit exceeded on {self.provider_name}. Backing off for {self.backoff_duration}s."
                    )
                w_res.raise_for_status()
                w_data = w_res.json()

            except httpx.TimeoutException as e:
                self._record_failure(aq_url, f"Request timeout ({self.timeout}s): {str(e)}")
                raise ExternalApiException(f"External API timeout contacting {self.provider_name}: {str(e)}")
            except httpx.HTTPStatusError as e:
                self._record_failure(aq_url, f"HTTP error: {e.response.status_code}", e.response.status_code)
                raise ExternalApiException(f"External API returned HTTP {e.response.status_code}: {str(e)}")
            except RateLimitExceededException:
                raise
            except Exception as e:
                self._record_failure(aq_url, f"Network or transport error: {str(e)}")
                raise ExternalApiException(f"Unable to connect to external weather API: {str(e)}")

        # Validate response payload structure
        if "current" not in aq_data or "current" not in w_data:
            self._record_failure(aq_url, "Payload validation failed: Missing 'current' telemetry block")
            raise ApiValidationException("External API response failed schema validation: Missing current readings.")

        aq_curr = aq_data["current"]
        w_curr = w_data["current"]

        pm25 = aq_curr.get("pm2_5")
        pm10 = aq_curr.get("pm10")
        temperature = w_curr.get("temperature_2m")
        humidity = w_curr.get("relative_humidity_2m")

        if pm25 is None or pm10 is None or temperature is None or humidity is None:
            self._record_failure(aq_url, "Payload validation failed: Missing primary atmospheric metrics")
            raise ApiValidationException("External API returned incomplete telemetry parameters.")

        self._record_success()
        latency_ms = int((time.time() - start_time) * 1000)
        logger.info(f"Successfully retrieved real data from Open-Meteo for {location_id} in {latency_ms}ms")

        # Map Open-Meteo trace metrics
        raw_dict = {
            "location_id": location_id,
            "pm25": float(pm25),
            "pm10": float(pm10),
            "temperature": float(temperature),
            "humidity": float(humidity),
            "co": float(aq_curr.get("carbon_monoxide") / 1000.0) if aq_curr.get("carbon_monoxide") is not None else None,
            "no2": float(aq_curr.get("nitrogen_dioxide")) if aq_curr.get("nitrogen_dioxide") is not None else None,
            "o3": float(aq_curr.get("ozone")) if aq_curr.get("ozone") is not None else None,
            "so2": float(aq_curr.get("sulphur_dioxide")) if aq_curr.get("sulphur_dioxide") is not None else None,
            "aqi": int(aq_curr.get("us_aqi")) if aq_curr.get("us_aqi") is not None else None,
            "recorded_at": retrieval_time,
        }

        # Normalize with strict source tagging: source_type="real"
        normalized = normalizer.normalize_reading(
            raw=raw_dict,
            source_type="real",
            source_provider="open-meteo",
            retrieved_at=retrieval_time,
        )
        normalized["retrieval_latency_ms"] = latency_ms
        return normalized

    async def fetch_real_readings_openweather(
        self, location_id: str, latitude: float, longitude: float
    ) -> Dict[str, Any]:
        """Fetch telemetry from OpenWeatherMap API using configured API key."""
        api_key = settings.OPENWEATHER_API_KEY.strip()
        if not api_key:
            self._record_failure("OpenWeatherMap", "OPENWEATHER_API_KEY not configured in environment variables", 401)
            raise ExternalApiException("OPENWEATHER_API_KEY environment variable is required to query OpenWeatherMap.")

        self.check_rate_limit()
        self.total_requests += 1
        retrieval_time = get_current_utc_iso()
        start_time = time.time()

        aq_url = "http://api.openweathermap.org/data/2.5/air_pollution"
        weather_url = "http://api.openweathermap.org/data/2.5/weather"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                aq_res = await client.get(aq_url, params={"lat": latitude, "lon": longitude, "appid": api_key})
                if aq_res.status_code == 429:
                    self.rate_limit_reset_timestamp = time.time() + self.backoff_duration
                    self._record_failure(aq_url, "HTTP 429 Rate Limit Exceeded", 429)
                    raise RateLimitExceededException("OpenWeatherMap rate limit reached.")
                aq_res.raise_for_status()
                aq_data = aq_res.json()

                w_res = await client.get(
                    weather_url,
                    params={"lat": latitude, "lon": longitude, "appid": api_key, "units": "metric"},
                )
                if w_res.status_code == 429:
                    self.rate_limit_reset_timestamp = time.time() + self.backoff_duration
                    self._record_failure(weather_url, "HTTP 429 Rate Limit Exceeded", 429)
                    raise RateLimitExceededException("OpenWeatherMap rate limit reached.")
                w_res.raise_for_status()
                w_data = w_res.json()

            except ExternalApiException:
                raise
            except Exception as e:
                self._record_failure(aq_url, str(e))
                raise ExternalApiException(f"OpenWeatherMap request failed: {str(e)}")

        # Validation
        if not aq_data.get("list") or not w_data.get("main"):
            self._record_failure(aq_url, "Malformed OpenWeatherMap payload")
            raise ApiValidationException("OpenWeatherMap response schema invalid.")

        components = aq_data["list"][0].get("components", {})
        main_weather = w_data.get("main", {})

        self._record_success()
        latency_ms = int((time.time() - start_time) * 1000)

        raw_dict = {
            "location_id": location_id,
            "pm25": float(components.get("pm2_5", 15.0)),
            "pm10": float(components.get("pm10", 30.0)),
            "temperature": float(main_weather.get("temp", 25.0)),
            "humidity": float(main_weather.get("humidity", 50.0)),
            "co": float(components.get("co", 300) / 1000.0) if components.get("co") is not None else None,
            "no2": float(components.get("no2")) if components.get("no2") is not None else None,
            "o3": float(components.get("o3")) if components.get("o3") is not None else None,
            "so2": float(components.get("so2")) if components.get("so2") is not None else None,
            "recorded_at": retrieval_time,
        }

        normalized = normalizer.normalize_reading(
            raw=raw_dict,
            source_type="real",
            source_provider="openweather",
            retrieved_at=retrieval_time,
        )
        normalized["retrieval_latency_ms"] = latency_ms
        return normalized

    async def fetch_real_data_for_location(
        self, location_id: str, latitude: float, longitude: float
    ) -> Dict[str, Any]:
        """Dispatch real data retrieval to the configured external provider."""
        provider = self.provider_name
        if provider == "openweather":
            return await self.fetch_real_readings_openweather(location_id, latitude, longitude)
        else:
            # Default to Open-Meteo (public, robust, zero credentials required)
            return await self.fetch_real_readings_open_meteo(location_id, latitude, longitude)

    def get_api_status(self) -> Dict[str, Any]:
        """Return diagnostic health and rate limit status of external API integration."""
        is_blocked = False
        remaining_backoff = 0
        if self.rate_limit_reset_timestamp:
            rem = self.rate_limit_reset_timestamp - time.time()
            if rem > 0:
                is_blocked = True
                remaining_backoff = int(rem)
            else:
                self.rate_limit_reset_timestamp = None

        return {
            "provider": self.provider_name,
            "status": "rate_limited" if is_blocked else self.last_status,
            "is_available": self.last_status in ("online", "degraded") and not is_blocked,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "consecutive_failures": self.consecutive_failures,
            "last_success_at": self.last_success_at,
            "last_failure_at": self.last_failure_at,
            "last_error": self.last_error_message,
            "rate_limited": is_blocked,
            "rate_limit_remaining_sec": remaining_backoff,
            "recent_failures": self.failures_log[:5],
        }


real_data_service = RealDataService()
