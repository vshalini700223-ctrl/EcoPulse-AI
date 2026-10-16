"""Test suite for EcoPulse AI FastAPI Backend Endpoints."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data
    assert "collections" in data["database"]
    print("[PASS] GET /api/health passed")


def test_locations():
    # GET locations
    response = client.get("/api/locations")
    assert response.status_code == 200
    locations = response.json()
    assert isinstance(locations, list)
    assert len(locations) > 0
    print(f"[PASS] GET /api/locations passed ({len(locations)} locations found)")

    # POST location
    new_loc = {
        "name": "EcoStation Zeta — Highland Ridge",
        "zone": "Mountain Biosphere",
        "location_type": "Highland",
        "latitude": 13.1205,
        "longitude": 77.8104,
        "status": "Active",
        "active_sensors": 10,
        "total_sensors": 10
    }
    create_res = client.post("/api/locations", json=new_loc)
    assert create_res.status_code == 201, f"Expected 201, got {create_res.status_code}: {create_res.text}"
    created = create_res.json()
    assert created["name"] == new_loc["name"]
    assert "id" in created
    print("[PASS] POST /api/locations passed")


def test_readings():
    # GET readings with pagination
    response = client.get("/api/readings?page=1&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert "page" in data
    assert data["page"] == 1
    assert len(data["items"]) <= 5
    print(f"[PASS] GET /api/readings with pagination passed ({data['total']} total records)")

    # Test filtering by location_id
    filter_res = client.get("/api/readings?location_id=station-alpha")
    assert filter_res.status_code == 200
    filter_data = filter_res.json()
    for item in filter_data["items"]:
        assert item["location_id"] == "station-alpha"
    print("[PASS] GET /api/readings filtered by location passed")

    # POST reading
    new_reading = {
        "location_id": "station-alpha",
        "pm25": 14.5,
        "pm10": 28.0,
        "aqi": 45,
        "temperature": 22.4,
        "humidity": 75.0,
        "co2": 405.0,
        "no2": 16.0,
        "o3": 24.0
    }
    create_res = client.post("/api/readings", json=new_reading)
    assert create_res.status_code == 201, f"Expected 201, got {create_res.status_code}: {create_res.text}"
    created = create_res.json()
    assert created["aqi"] == 45
    assert created["aqi_category"] == "Good"
    assert "id" in created
    print("[PASS] POST /api/readings passed with automated AQI category assignment")


def test_alerts():
    # GET alerts
    response = client.get("/api/alerts")
    assert response.status_code == 200
    alerts = response.json()
    assert isinstance(alerts, list)
    print(f"[PASS] GET /api/alerts passed ({len(alerts)} alerts found)")

    # POST alert
    new_alert = {
        "location_id": "station-beta",
        "title": "High Thermal Inversion Detected",
        "severity": "warning",
        "metric_name": "Inversion Trapping",
        "metric_value": "82% Probability",
        "threshold_description": "Exceeds 70% risk threshold",
        "status": "Active"
    }
    create_res = client.post("/api/alerts", json=new_alert)
    assert create_res.status_code == 201, f"Expected 201, got {create_res.status_code}: {create_res.text}"
    created = create_res.json()
    assert created["title"] == new_alert["title"]
    assert "id" in created
    print("[PASS] POST /api/alerts passed")


def test_analytics_summary():
    response = client.get("/api/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_locations" in data
    assert "total_readings" in data
    assert "average_aqi" in data
    assert "environmental_grade" in data
    print(f"[PASS] GET /api/analytics/summary passed (Avg AQI: {data['average_aqi']}, Grade: {data['environmental_grade']})")


def test_seed():
    response = client.post("/api/seed")
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert "seeded" in data
    print(f"[PASS] POST /api/seed passed (Seeded collections: {data['seeded']})")


def test_ingestion_and_deduplication():
    # 1. Ingest new reading
    reading_payload = {
        "location_id": "station-beta",
        "pm25": 32.5,
        "pm10": 65.0,
        "temperature": 27.2,
        "humidity": 55.0,
        "co2": 440.0,
        "timestamp": "2026-10-03T10:00:00Z",
        "source_type": "simulated",
        "source_provider": "ecopulse-test-runner"
    }
    res = client.post("/api/ingestion/reading", json=reading_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["status"] == "success"
    assert data["is_duplicate"] is False
    assert data["reading"]["location_id"] == "station-beta"
    assert data["reading"]["source_type"] == "simulated"
    assert data["reading"]["aqi_category"] in ("Moderate", "Good", "Unhealthy for Sensitive Groups")
    print("[PASS] POST /api/ingestion/reading passed with normalization and AQI calculation")

    # 2. Duplicate detection check: post identical reading again
    dup_res = client.post("/api/ingestion/reading", json=reading_payload)
    assert dup_res.status_code == 201
    dup_data = dup_res.json()
    assert dup_data["status"] == "duplicate_skipped"
    assert dup_data["is_duplicate"] is True
    print("[PASS] Duplicate ingestion successfully detected and blocked!")


def test_batch_ingestion():
    batch = [
        {
            "location_id": "station-alpha",
            "pm25": 8.5,
            "pm10": 17.0,
            "temperature": 21.5,
            "humidity": 78.0,
            "timestamp": "2026-10-03T10:05:00Z",
            "source_type": "real",
            "source_provider": "open-meteo"
        },
        {
            "location_id": "station-delta",
            "pm25": 11.2,
            "pm10": 24.0,
            "temperature": 23.8,
            "humidity": 82.0,
            "timestamp": "2026-10-03T10:05:00Z",
            "source_type": "real",
            "source_provider": "open-meteo"
        }
    ]
    res = client.post("/api/ingestion/batch", json=batch)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "completed"
    assert data["total_submitted"] == 2
    assert data["ingested_count"] >= 1
    print(f"[PASS] POST /api/ingestion/batch passed ({data['ingested_count']} ingested, {data['duplicates_skipped']} skipped)")


def test_simulation_lifecycle():
    # Query simulator status
    status_res = client.get("/api/ingestion/simulate/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert "is_running" in status_data

    # Start simulator with 5 second interval
    start_res = client.post("/api/ingestion/simulate/start?interval=5")
    assert start_res.status_code == 200
    start_data = start_res.json()
    assert start_data["status"] in ("started", "already_running")
    print(f"[PASS] POST /api/ingestion/simulate/start passed (Interval: {start_data['interval_seconds']}s)")

    # Stop simulator safely
    stop_res = client.post("/api/ingestion/simulate/stop")
    assert stop_res.status_code == 200
    stop_data = stop_res.json()
    assert stop_data["status"] in ("stopped", "not_running")
    print("[PASS] POST /api/ingestion/simulate/stop passed safely")


def test_telemetry_sources_status():
    res = client.get("/api/ingestion/status")
    assert res.status_code == 200
    data = res.json()
    assert "external_api" in data
    assert "simulator" in data
    assert "records_by_source" in data
    assert data["external_api"]["provider"] in ("open-meteo", "openweather", "waqi")
    print(f"[PASS] GET /api/ingestion/status passed (API Provider: {data['external_api']['provider']}, State: {data['external_api']['status']})")


def test_historical_readings_and_seeding():
    # 1. Seed historical data for 2 days
    seed_res = client.post("/api/ingestion/historical/seed?days=2")
    assert seed_res.status_code == 200
    seed_data = seed_res.json()
    assert seed_data["status"] == "success"
    assert seed_data["ingested_count"] > 0
    print(f"[PASS] POST /api/ingestion/historical/seed passed ({seed_data['ingested_count']} historical records created)")

    # 2. Query historical readings endpoint
    hist_res = client.get("/api/readings/history?limit=50")
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert "total_records" in hist_data
    assert "average_aqi" in hist_data
    assert hist_data["total_records"] > 0
    assert len(hist_data["items"]) > 0
    print(f"[PASS] GET /api/readings/history passed ({hist_data['total_records']} total records, Avg AQI: {hist_data['average_aqi']})")

    # 3. Query readings filtered by source_type
    filter_res = client.get("/api/readings?source_type=historical&limit=10")
    assert filter_res.status_code == 200
    filter_data = filter_res.json()
    for item in filter_data["items"]:
        assert item["source_type"] == "historical"
    print(f"[PASS] GET /api/readings?source_type=historical passed ({filter_data['total']} historical records matched)")


def test_forecast_endpoints():
    """Verify ML pollution forecasting endpoints, metadata, predictions, and evaluation."""
    # 1. Model Status
    status_res = client.get("/api/forecast/model-status")
    assert status_res.status_code == 200, f"Expected 200, got {status_res.status_code}"
    status_data = status_res.json()
    assert status_data["is_trained"] is True
    assert "metrics" in status_data
    assert "model_mae" in status_data["metrics"]
    assert "model_rmse" in status_data["metrics"]
    assert "model_limitations" in status_data
    print(f"[PASS] GET /api/forecast/model-status passed (Model: {status_data['model_name']}, MAE: {status_data['metrics']['model_mae']})")

    # 2. Multi-step Forecast (24h)
    predict_res = client.post("/api/forecast/predict", json={
        "location_id": "station-beta",
        "horizon_hours": 24,
    })
    assert predict_res.status_code == 200, f"Expected 200, got {predict_res.status_code}"
    predict_data = predict_res.json()
    assert len(predict_data["forecast_points"]) == 24
    assert len(predict_data["historical_measurements"]) > 0
    assert "limitations_notice" in predict_data
    assert "data_source_type" in predict_data
    # Verify uncertainty interval exists
    first_pt = predict_data["forecast_points"][0]
    assert "predicted_pm25" in first_pt
    assert "pm25_lower" in first_pt
    assert "pm25_upper" in first_pt
    assert first_pt["pm25_lower"] <= first_pt["predicted_pm25"] <= first_pt["pm25_upper"]
    print(f"[PASS] POST /api/forecast/predict (24h) passed ({len(predict_data['forecast_points'])} steps generated)")

    # 3. Extended Forecast (48h)
    predict_48_res = client.post("/api/forecast/predict", json={
        "location_id": "station-alpha",
        "horizon_hours": 48,
    })
    assert predict_48_res.status_code == 200
    assert len(predict_48_res.json()["forecast_points"]) == 48
    print("[PASS] POST /api/forecast/predict (48h) passed")

    # 4. Holdout Evaluation Series
    eval_res = client.get("/api/forecast/evaluation")
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert "test_series" in eval_data
    assert len(eval_data["test_series"]) > 0
    print(f"[PASS] GET /api/forecast/evaluation passed ({len(eval_data['test_series'])} holdout points)")


if __name__ == "__main__":
    print("\n========== Running EcoPulse AI Backend Test Suite ==========\n")
    test_health()
    test_locations()
    test_readings()
    test_alerts()
    test_analytics_summary()
    test_seed()
    test_ingestion_and_deduplication()
    test_batch_ingestion()
    test_simulation_lifecycle()
    test_telemetry_sources_status()
    test_historical_readings_and_seeding()
    test_forecast_endpoints()
    print("\n========== All Backend API Endpoints & Ingestion Suite Passed Successfully! ==========\n")

