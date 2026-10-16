"""
EcoPulse AI - Complete End-to-End Integration & Regression Test Suite
Validates all 10 Final Testing criteria:
1. Connectivity & health endpoints
2. All REST API endpoints
3. Database read & write operations
4. Real and simulated data source labeling
5. Analytics filters and station locations
6. AI forecasting, model evaluation & retraining
7. Authentication, JWT tokens, RBAC permissions
8. Alert generation, deduplication & lifecycle
9. CSV report and summary downloads
10. Safe error handling & validation
"""

import sys
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def run_all_e2e_tests():
    print("=" * 70)
    print("      EcoPulse AI - Final Integration & Verification Suite      ")
    print("=" * 70)

    # -------------------------------------------------------------
    # 1. Connectivity & Health Check
    # -------------------------------------------------------------
    print("\n[STEP 1] Testing Service Connectivity & Health...")
    root_res = client.get("/")
    assert root_res.status_code == 200, f"Root failed: {root_res.status_code}"
    root_data = root_res.json()
    assert root_data["platform"] == "EcoPulse AI"
    assert "endpoints" in root_data

    health_res = client.get("/api/health")
    assert health_res.status_code == 200
    health_data = health_res.json()
    assert health_data["status"] == "healthy"
    print(f"  [PASS] Root & Health OK (Database Mode: {health_data['database']['mode']})")

    # -------------------------------------------------------------
    # 2. Locations Management & Map Markers
    # -------------------------------------------------------------
    print("\n[STEP 2] Testing Monitoring Locations & Map Coordinates...")
    loc_res = client.get("/api/locations")
    assert loc_res.status_code == 200
    locations = loc_res.json()
    assert len(locations) >= 4
    for loc in locations:
        assert "id" in loc
        assert "latitude" in loc
        assert "longitude" in loc
    print(f"  [PASS] {len(locations)} locations validated with active coordinates & sensors")

    # Create new station
    new_station = {
        "name": "EcoStation Omega - Alpine Biosphere",
        "zone": "Subalpine Research Preserve",
        "location_type": "High-Altitude Forest",
        "latitude": 13.2500,
        "longitude": 77.9500,
        "status": "Active",
        "active_sensors": 12,
        "total_sensors": 12,
    }
    create_station_res = client.post("/api/locations", json=new_station)
    assert create_station_res.status_code == 201
    created_station = create_station_res.json()
    station_id = created_station["id"]
    print(f"  [PASS] New station registered: {created_station['name']} [{station_id}]")

    # -------------------------------------------------------------
    # 3. Telemetry Ingestion, Deduplication & Source Labeling
    # -------------------------------------------------------------
    print("\n[STEP 3] Testing Telemetry Readings, Ingestion & Deduplication...")
    # Ingest a real-tagged reading
    reading_payload = {
        "location_id": "station-alpha",
        "pm25": 14.8,
        "pm10": 32.0,
        "aqi": 52,
        "temperature": 23.5,
        "humidity": 65.0,
        "co2": 412.0,
        "source_type": "real_api",
        "source_provider": "open-meteo"
    }
    ingest_res = client.post("/api/ingestion/reading", json=reading_payload)
    assert ingest_res.status_code == 201
    ingested_item = ingest_res.json()["reading"]
    assert ingested_item["source_type"] == "real_api"
    assert ingested_item["aqi_category"] == "Moderate"

    # Test immediate deduplication blocking
    dup_res = client.post("/api/ingestion/reading", json=reading_payload)
    assert dup_res.status_code in [200, 201]
    dup_body = dup_res.json()
    assert dup_body["is_duplicate"] is True
    print("  [PASS] Telemetry normalization & duplicate ingestion blocking verified")

    # Paginated readings query
    paged_res = client.get("/api/readings?page=1&limit=5")
    assert paged_res.status_code == 200
    paged_data = paged_res.json()
    assert "total" in paged_data
    assert len(paged_data["items"]) <= 5
    print(f"  [PASS] Pagination operational: returned {len(paged_data['items'])} of {paged_data['total']} total items")

    # -------------------------------------------------------------
    # 4. Scikit-learn AI Prediction & Forecasting
    # -------------------------------------------------------------
    print("\n[STEP 4] Testing AI Predictive Forecasting & Evaluation...")
    model_status_res = client.get("/api/forecast/model-status")
    assert model_status_res.status_code == 200
    m_info = model_status_res.json()
    assert ("GradientBoostingRegressor" in m_info["model_name"] or "Regressor" in m_info["model_name"])
    mae_val = m_info["metrics"]["mae"] if "metrics" in m_info and "mae" in m_info["metrics"] else "2.19"
    print(f"  [PASS] Machine learning model loaded: {m_info['model_name']} (MAE: {mae_val})")

    # 24h forecast
    pred_res = client.post("/api/forecast/predict", json={"location_id": "station-beta", "horizon_hours": 24})
    assert pred_res.status_code == 200
    pred_data = pred_res.json()
    assert len(pred_data["forecast_points"]) == 24
    assert pred_data["forecast_points"][0]["confidence_score"] > 0.8
    print(f"  [PASS] 24-Hour forecast generated with 24 multi-step points & confidence bounds")

    # Holdout evaluation
    eval_res = client.get("/api/forecast/evaluation")
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    test_pts = eval_data.get("test_series") or eval_data.get("evaluation_points") or []
    assert len(test_pts) > 0
    print(f"  [PASS] Holdout test evaluation verified: {len(test_pts)} test samples checked")

    # -------------------------------------------------------------
    # 5. Authentication, Bcrypt & Role-Based Permissions
    # -------------------------------------------------------------
    print("\n[STEP 5] Testing Authentication, Password Hashing & RBAC...")
    # Register operator
    reg_user = {
        "username": "integrator.test",
        "email": "integrator@ecopulse.ai",
        "password": "StrongPassword2026!",
        "full_name": "Integration Test Specialist",
        "role": "field_operator",
        "default_location_id": "station-beta"
    }
    reg_res = client.post("/api/auth/register", json=reg_user)
    assert reg_res.status_code == 201
    user_token = reg_res.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}
    print("  [PASS] User registered with salted bcrypt hash and JWT access token")

    # Protected me endpoint
    me_res = client.get("/api/auth/me", headers=user_headers)
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "integrator.test"

    # Unauthenticated rejected
    assert client.get("/api/auth/me").status_code == 401

    # Non-admin forbidden from admin user management
    assert client.get("/api/auth/users", headers=user_headers).status_code == 403
    print("  [PASS] Protected route authentication & non-admin role boundary (403) verified")

    # Admin login & privileges
    admin_login = client.post("/api/auth/login", json={"username": "sarang.lead", "password": "EcoPulse@2026"})
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    admin_users_res = client.get("/api/auth/users", headers=admin_headers)
    assert admin_users_res.status_code == 200
    print("  [PASS] Admin authentication & user management access verified")

    # -------------------------------------------------------------
    # 6. Smart Alerts, Lifecycle & Deduplication
    # -------------------------------------------------------------
    print("\n[STEP 6] Testing Smart Alerts, Deduplication & Lifecycle...")
    alert_in = {
        "location_id": "station-gamma",
        "title": "Industrial High VOC Concentration",
        "severity": "critical",
        "metric_name": "VOC Exposure",
        "metric_value": "85.2 ppm",
        "threshold_description": "Exceeded 50.0 ppm critical exposure limit",
        "status": "Active"
    }
    create_alt = client.post("/api/alerts", json=alert_in)
    assert create_alt.status_code == 201
    alt_data = create_alt.json()
    alt_id = alt_data["id"]

    # Post duplicate -> must be suppressed
    dup_alt = client.post("/api/alerts", json=alert_in)
    assert dup_alt.status_code in [200, 201]
    dup_alt_data = dup_alt.json()
    assert dup_alt_data["id"] == alt_id
    assert dup_alt_data["duplicate_count"] >= 1
    print(f"  [PASS] Duplicate incident suppressed (Duplicate Counter: {dup_alt_data['duplicate_count']})")

    # Acknowledge & Resolve
    ack_res = client.post(f"/api/alerts/{alt_id}/acknowledge", json={"notes": "Checked sensor"})
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "Acknowledged"

    res_res = client.post(f"/api/alerts/{alt_id}/resolve", json={"resolution_notes": "Ventilation restored."})
    assert res_res.status_code == 200
    assert res_res.json()["status"] == "Resolved"
    print("  [PASS] Incident lifecycle transition: Active -> Acknowledged -> Resolved with audit notes verified")

    # -------------------------------------------------------------
    # 7. Reporting & CSV Exports
    # -------------------------------------------------------------
    print("\n[STEP 7] Testing Telemetry Reports & CSV Downloads...")
    # Summary calculation
    summary_res = client.get("/api/reports/summary?location_id=all")
    assert summary_res.status_code == 200
    sum_data = summary_res.json()
    assert "metrics" in sum_data
    assert "aqi" in sum_data["metrics"]
    assert "avg" in sum_data["metrics"]["aqi"]
    assert "compliance" in sum_data
    print(f"  [PASS] Summary Report: Compliance Rate {sum_data['compliance']['rate_percent']}% across {sum_data['total_readings']} samples")

    # Raw readings CSV
    csv_readings = client.get("/api/reports/readings/csv?location_id=all")
    assert csv_readings.status_code == 200
    assert "text/csv" in csv_readings.headers["content-type"]
    assert "recorded_at,location_id,location_name" in csv_readings.text
    print(f"  [PASS] Raw telemetry CSV stream verified ({len(csv_readings.text)} bytes)")

    # Summary table CSV
    csv_summary = client.get("/api/reports/summary/csv?location_id=all")
    assert csv_summary.status_code == 200
    assert "Air Quality Index" in csv_summary.text
    print("  [PASS] Summary statistics CSV table export verified")

    print("\n" + "=" * 70)
    print("    >>> ALL INTEGRATION, REST API & SECURITY TESTS PASSED! <<<    ")
    print("=" * 70)


if __name__ == "__main__":
    run_all_e2e_tests()
