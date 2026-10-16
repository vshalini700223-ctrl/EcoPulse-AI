"""Comprehensive test suite for Authentication, Smart Alerts, and Reporting modules."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_auth_registration_and_login():
    print("\n--- Testing Authentication & Authorization ---")
    
    # 1. Register a new user
    new_user_data = {
        "username": "tester.eco",
        "email": "tester@ecopulse.ai",
        "password": "SecurePassword123!",
        "full_name": "Field Monitoring Operator",
        "role": "field_operator",
        "default_location_id": "station-beta"
    }
    reg_res = client.post("/api/auth/register", json=new_user_data)
    assert reg_res.status_code == 201, f"Register failed: {reg_res.text}"
    reg_json = reg_res.json()
    assert "access_token" in reg_json
    assert reg_json["token_type"] == "bearer"
    assert "hashed_password" not in reg_json["user"]
    assert reg_json["user"]["username"] == "tester.eco"
    assert reg_json["user"]["role"] == "field_operator"
    print("[PASS] User registration passed with secure token issuance")

    token = reg_json["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 2. Duplicate registration rejection
    dup_res = client.post("/api/auth/register", json=new_user_data)
    assert dup_res.status_code == 400
    print("[PASS] Duplicate registration prevented")

    # 3. Login with credentials
    login_res = client.post("/api/auth/login", json={
        "username": "tester.eco",
        "password": "SecurePassword123!"
    })
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()
    print("[PASS] User login with valid credentials passed")

    # 4. Login with invalid password
    bad_login = client.post("/api/auth/login", json={
        "username": "tester.eco",
        "password": "WrongPassword!"
    })
    assert bad_login.status_code == 401
    print("[PASS] Login with invalid password rejected (401)")

    # 5. Access protected /me endpoint
    me_res = client.get("/api/auth/me", headers=auth_headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "tester@ecopulse.ai"
    print("[PASS] Protected /api/auth/me returned authenticated profile")

    # 6. Unauthenticated request to /me
    unauth_res = client.get("/api/auth/me")
    assert unauth_res.status_code == 401
    print("[PASS] Unauthenticated request to protected endpoint blocked (401)")

    # 7. Update profile and preferences
    update_res = client.put("/api/auth/profile", headers=auth_headers, json={
        "full_name": "Senior Field Specialist",
        "default_location_id": "station-gamma",
        "notification_preferences": {
            "email_alerts": True,
            "in_app_alerts": True,
            "minimum_severity": "critical",
            "digest_frequency": "daily"
        }
    })
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["full_name"] == "Senior Field Specialist"
    assert updated_data["default_location_id"] == "station-gamma"
    assert updated_data["notification_preferences"]["minimum_severity"] == "critical"
    print("[PASS] Profile and notification preferences update passed")

    # 8. Change password
    pwd_res = client.post("/api/auth/change-password", headers=auth_headers, json={
        "current_password": "SecurePassword123!",
        "new_password": "NewSecretPassword2026!"
    })
    assert pwd_res.status_code == 200
    print("[PASS] Password change passed")

    # 9. Verify login with new password
    new_login = client.post("/api/auth/login", json={
        "username": "tester.eco",
        "password": "NewSecretPassword2026!"
    })
    assert new_login.status_code == 200
    print("[PASS] Login with new password succeeded")

    # 10. Role-based access control (RBAC): Field operator cannot list users
    forbidden_res = client.get("/api/auth/users", headers=auth_headers)
    assert forbidden_res.status_code == 403
    print("[PASS] Non-admin user blocked from admin endpoint (403 Forbidden)")

    # 11. Admin login with seed user
    admin_login = client.post("/api/auth/login", json={
        "username": "sarang.lead",
        "password": "EcoPulse@2026"
    })
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 12. Admin access to list users
    admin_users_res = client.get("/api/auth/users", headers=admin_headers)
    assert admin_users_res.status_code == 200
    users_list = admin_users_res.json()
    assert len(users_list) >= 2
    print(f"[PASS] Admin RBAC validated ({len(users_list)} platform users listed)")


def test_smart_alerts():
    print("\n--- Testing Smart Alerts & Incident Lifecycle ---")

    # 1. Fetch alert stats
    stats_res = client.get("/api/alerts/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert "total" in stats
    assert "active" in stats
    print(f"[PASS] GET /api/alerts/stats passed (Active: {stats['active']}, Total: {stats['total']})")

    # 2. Thresholds configuration
    thresh_res = client.get("/api/alerts/thresholds")
    assert thresh_res.status_code == 200
    thresh = thresh_res.json()
    assert "pm25" in thresh
    assert thresh["pm25"]["warning"] == 35.0
    print("[PASS] GET /api/alerts/thresholds passed")

    # 3. Create a unique alert
    alert_payload = {
        "location_id": "station-delta",
        "title": "Severe Ozone Photochemical Spike",
        "severity": "critical",
        "metric_name": "Ozone O3",
        "metric_value": "180 µg/m³",
        "threshold_description": "Exceeded 120 µg/m³ critical ceiling",
        "status": "Active"
    }
    create_res = client.post("/api/alerts", json=alert_payload)
    assert create_res.status_code == 201
    created = create_res.json()
    alert_id = created["id"]
    assert created["status"] == "Active"
    assert created["duplicate_count"] == 0
    print(f"[PASS] POST /api/alerts created incident {alert_id}")

    # 4. Duplicate alert prevention: Post identical active alert for same station & metric
    dup_alert_payload = {
        "location_id": "station-delta",
        "title": "Severe Ozone Photochemical Spike",
        "severity": "critical",
        "metric_name": "Ozone O3",
        "metric_value": "185 µg/m³",
        "threshold_description": "Exceeded 120 µg/m³ critical ceiling",
        "status": "Active"
    }
    dup_create_res = client.post("/api/alerts", json=dup_alert_payload)
    assert dup_create_res.status_code in [200, 201]
    dup_created = dup_create_res.json()
    assert dup_created["id"] == alert_id, "Duplicate alert was created instead of updating existing!"
    assert dup_created["duplicate_count"] >= 1
    assert dup_created["metric_value"] == "185 µg/m³"
    print(f"[PASS] Duplicate alert prevention verified (Counter: {dup_created['duplicate_count']})")

    # 5. Acknowledge alert
    ack_res = client.post(f"/api/alerts/{alert_id}/acknowledge", json={"notes": "Dispatched field sensor inspection"})
    assert ack_res.status_code == 200
    acked = ack_res.json()
    assert acked["status"] == "Acknowledged"
    assert acked["acknowledged_at"] is not None
    print(f"[PASS] POST /api/alerts/{alert_id}/acknowledge passed")

    # 6. Resolve alert
    res_res = client.post(f"/api/alerts/{alert_id}/resolve", json={"resolution_notes": "Scrubber reactivated. Levels normalized."})
    assert res_res.status_code == 200
    resolved = res_res.json()
    assert resolved["status"] == "Resolved"
    assert resolved["resolved_at"] is not None
    assert resolved["resolution_notes"] == "Scrubber reactivated. Levels normalized."
    print(f"[PASS] POST /api/alerts/{alert_id}/resolve passed with resolution audit")

    # 7. Evaluate reading thresholds automatically
    eval_res = client.post("/api/alerts/evaluate-reading", json={
        "location_id": "station-gamma",
        "pm25": 82.5,  # Breaches critical 75.0
        "pm10": 40.0,
        "aqi": 160,    # Breaches warning 100
        "co2": 500,
        "temperature": 25.0,
        "humidity": 60.0
    })
    assert eval_res.status_code == 200
    eval_alerts = eval_res.json()
    assert len(eval_alerts) >= 1
    print(f"[PASS] Automated telemetry threshold evaluation generated {len(eval_alerts)} alerts")


def test_reporting():
    print("\n--- Testing Reporting & Telemetry Exports ---")

    # 1. Summary Report Generation
    summary_res = client.get("/api/reports/summary?location_id=station-alpha")
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert "report_id" in summary
    assert "generation_timestamp" in summary
    assert "metrics" in summary
    assert "aqi" in summary["metrics"]
    assert "avg" in summary["metrics"]["aqi"]
    assert "min" in summary["metrics"]["aqi"]
    assert "max" in summary["metrics"]["aqi"]
    assert "compliance" in summary
    assert "rate_percent" in summary["compliance"]
    print(f"[PASS] GET /api/reports/summary passed (Station: {summary['filters']['location_name']}, Total: {summary['total_readings']})")
    print(f"       AQI Avg: {summary['metrics']['aqi']['avg']}, Min: {summary['metrics']['aqi']['min']}, Max: {summary['metrics']['aqi']['max']}")

    # 2. Historical CSV Export
    csv_res = client.get("/api/reports/readings/csv?location_id=station-alpha")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    assert "attachment" in csv_res.headers["content-disposition"]
    csv_text = csv_res.text
    assert "recorded_at" in csv_text
    assert "location_name" in csv_text
    assert "pm25_ug_m3" in csv_text
    print(f"[PASS] GET /api/reports/readings/csv returned downloadable CSV ({len(csv_text)} bytes)")

    # 3. Summary Statistics CSV Export
    summary_csv_res = client.get("/api/reports/summary/csv?location_id=all")
    assert summary_csv_res.status_code == 200
    assert "text/csv" in summary_csv_res.headers["content-type"]
    assert "Air Quality Index" in summary_csv_res.text
    print("[PASS] GET /api/reports/summary/csv returned formatted summary statistics table")

    # 4. Report Templates List
    tpl_res = client.get("/api/reports/templates")
    assert tpl_res.status_code == 200
    templates = tpl_res.json()
    assert len(templates) >= 4
    print(f"[PASS] GET /api/reports/templates returned {len(templates)} compliance audit packages")


if __name__ == "__main__":
    test_auth_registration_and_login()
    test_smart_alerts()
    test_reporting()
    print("\n========== ALL AUTHENTICATION, ALERT MANAGEMENT & REPORTING TESTS PASSED! ==========")
