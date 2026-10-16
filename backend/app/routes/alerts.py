import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query, status, HTTPException, Depends
from app.models.alert import (
    AlertCreate,
    AlertResponse,
    AlertAcknowledgeRequest,
    AlertResolveRequest,
    AlertThresholdConfig,
    AlertStatsResponse,
)
from app.models.common import generate_uuid, get_current_utc_iso
from app.services.database import db_manager
from app.services.auth_service import get_optional_current_user, get_current_user
from app.services.notification_service import dispatch_alert_notification

logger = logging.getLogger("ecopulse.routes.alerts")

router = APIRouter(prefix="/alerts", tags=["Smart Alerts"])


def resolve_station_name(location_id: str) -> str:
    """Find human-readable station name for a given location ID."""
    locations = db_manager.memory_store.get("monitoring_locations", [])
    for loc in locations:
        if loc.get("id") == location_id:
            return loc.get("name", location_id)
    return location_id


async def get_stored_thresholds() -> Dict[str, Any]:
    """Retrieve active alert thresholds from MongoDB Atlas or memory store."""
    if db_manager.is_connected and db_manager.thresholds is not None:
        try:
            doc = await db_manager.thresholds.find_one({"id": "system_thresholds"}, {"_id": 0})
            if doc and "config" in doc:
                return doc["config"]
        except Exception as e:
            logger.warning(f"Error fetching thresholds from db: {e}")
    
    return db_manager.memory_store.get("thresholds", AlertThresholdConfig().model_dump())


@router.get("", response_model=List[AlertResponse], summary="List Environmental Alerts")
async def get_alerts(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (Active, Acknowledged, Resolved)"),
    severity: Optional[str] = Query(None, description="Filter by severity (critical, warning, info)"),
    location_id: Optional[str] = Query(None, description="Filter by station location ID"),
):
    """Retrieve environmental incident alerts with status, severity, and station filters."""
    query = {}
    if status_filter:
        query["status"] = status_filter
    if severity:
        query["severity"] = severity.lower()
    if location_id:
        query["location_id"] = location_id

    if db_manager.is_connected and db_manager.alerts is not None:
        try:
            cursor = db_manager.alerts.find(query, {"_id": 0}).sort("created_at", -1)
            alerts = await cursor.to_list(length=150)
            return alerts
        except Exception as e:
            logger.warning(f"Error querying alerts collection: {e}")

    # In-memory store fallback
    alerts = db_manager.memory_store.get("alerts", [])
    filtered = []
    for a in alerts:
        if status_filter and a.get("status", "").lower() != status_filter.lower():
            continue
        if severity and a.get("severity", "").lower() != severity.lower():
            continue
        if location_id and a.get("location_id") != location_id:
            continue
        filtered.append(a)

    filtered.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return filtered


@router.get("/stats", response_model=AlertStatsResponse, summary="Get Alert Incident Statistics")
async def get_alert_stats():
    """Retrieve aggregated counts of active, acknowledged, resolved, and categorized alerts."""
    all_alerts = []
    if db_manager.is_connected and db_manager.alerts is not None:
        try:
            cursor = db_manager.alerts.find({}, {"_id": 0})
            all_alerts = await cursor.to_list(length=500)
        except Exception as e:
            logger.warning(f"Failed to fetch alert stats: {e}")
            all_alerts = db_manager.memory_store.get("alerts", [])
    else:
        all_alerts = db_manager.memory_store.get("alerts", [])

    total = len(all_alerts)
    active = sum(1 for a in all_alerts if a.get("status", "").lower() == "active")
    acknowledged = sum(1 for a in all_alerts if a.get("status", "").lower() == "acknowledged")
    resolved = sum(1 for a in all_alerts if a.get("status", "").lower() == "resolved")
    critical = sum(1 for a in all_alerts if a.get("severity", "").lower() == "critical")
    warning = sum(1 for a in all_alerts if a.get("severity", "").lower() == "warning")
    info = sum(1 for a in all_alerts if a.get("severity", "").lower() in ["info", "success"])

    return {
        "total": total,
        "active": active,
        "acknowledged": acknowledged,
        "resolved": resolved,
        "critical": critical,
        "warning": warning,
        "info": info,
    }


@router.get("/thresholds", response_model=AlertThresholdConfig, summary="Get Environmental Alert Thresholds")
async def get_thresholds():
    """Retrieve current system-wide environmental alert trigger limits."""
    thresh = await get_stored_thresholds()
    return AlertThresholdConfig(**thresh)


@router.put("/thresholds", response_model=AlertThresholdConfig, summary="Update Environmental Alert Thresholds")
async def update_thresholds(
    threshold_in: AlertThresholdConfig,
    current_user: Optional[dict] = Depends(get_optional_current_user),
):
    """Update system environmental parameter threshold triggers."""
    new_data = threshold_in.model_dump()
    db_manager.memory_store["thresholds"] = new_data

    if db_manager.is_connected and db_manager.thresholds is not None:
        try:
            await db_manager.thresholds.update_one(
                {"id": "system_thresholds"},
                {"$set": {"config": new_data, "updated_at": get_current_utc_iso()}},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error persisting updated thresholds: {e}")

    logger.info("Updated environmental alert thresholds successfully.")
    return AlertThresholdConfig(**new_data)


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED, summary="Create Environmental Alert")
async def create_alert(alert_in: AlertCreate):
    """
    Trigger a new environmental threshold incident alert with automated duplicate prevention.
    If an active alert for the same location and metric already exists, updates metric and increments duplicate counter.
    """
    # -------------------------------------------------------------
    # DUPLICATE ALERT PREVENTION
    # -------------------------------------------------------------
    loc_id = alert_in.location_id
    m_name = alert_in.metric_name

    # Check database or in-memory store for active duplicate
    if db_manager.is_connected and db_manager.alerts is not None:
        try:
            existing = await db_manager.alerts.find_one(
                {"location_id": loc_id, "metric_name": m_name, "status": "Active"},
                {"_id": 0}
            )
            if existing:
                # Update existing alert instead of creating duplicate
                dup_count = existing.get("duplicate_count", 0) + 1
                await db_manager.alerts.update_one(
                    {"id": existing["id"]},
                    {
                        "$set": {
                            "metric_value": alert_in.metric_value,
                            "severity": alert_in.severity.lower(),
                            "duplicate_count": dup_count,
                            "updated_at": get_current_utc_iso()
                        }
                    }
                )
                existing["metric_value"] = alert_in.metric_value
                existing["severity"] = alert_in.severity.lower()
                existing["duplicate_count"] = dup_count
                logger.info(f"Prevented duplicate alert for {loc_id} / {m_name}. Updated counter: {dup_count}")
                return AlertResponse(**existing)
        except Exception as e:
            logger.warning(f"Error checking duplicate alert in db: {e}")

    # Check in-memory store for duplicate
    alerts = db_manager.memory_store.get("alerts", [])
    for a in alerts:
        if a.get("location_id") == loc_id and a.get("metric_name") == m_name and a.get("status") == "Active":
            a["duplicate_count"] = a.get("duplicate_count", 0) + 1
            a["metric_value"] = alert_in.metric_value
            a["severity"] = alert_in.severity.lower()
            a["updated_at"] = get_current_utc_iso()
            logger.info(f"Prevented duplicate alert in memory store for {loc_id} / {m_name}.")
            return AlertResponse(**a)

    # -------------------------------------------------------------
    # CREATE NEW ALERT
    # -------------------------------------------------------------
    alert_id = f"alt-{generate_uuid()[:8]}"
    created_at = get_current_utc_iso()
    loc_name = resolve_station_name(alert_in.location_id)

    new_alert = {
        "id": alert_id,
        "location_id": alert_in.location_id,
        "location_name": loc_name,
        "title": alert_in.title,
        "severity": alert_in.severity.lower(),
        "metric_name": alert_in.metric_name,
        "metric_value": alert_in.metric_value,
        "threshold_description": alert_in.threshold_description,
        "status": alert_in.status,
        "created_at": created_at,
        "acknowledged_at": None,
        "acknowledged_by": None,
        "resolved_at": None,
        "resolved_by": None,
        "resolution_notes": None,
        "duplicate_count": 0,
    }

    if db_manager.is_connected and db_manager.alerts is not None:
        try:
            await db_manager.alerts.insert_one(dict(new_alert))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error during alert creation: {str(e)}")
    else:
        db_manager.memory_store["alerts"].insert(0, new_alert)

    # Dispatch notification (async email or log simulation)
    try:
        await dispatch_alert_notification(new_alert)
    except Exception as e:
        logger.warning(f"Notification dispatch notice: {e}")

    return AlertResponse(**new_alert)


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse, summary="Acknowledge Alert")
async def acknowledge_alert(
    alert_id: str,
    ack_req: Optional[AlertAcknowledgeRequest] = None,
    current_user: Optional[dict] = Depends(get_optional_current_user),
):
    """Mark an active environmental incident as acknowledged by an operator."""
    operator_name = current_user.get("username") if current_user else "Environmental Operator"
    ack_time = get_current_utc_iso()

    updates = {
        "status": "Acknowledged",
        "acknowledged_at": ack_time,
        "acknowledged_by": operator_name,
    }

    if db_manager.is_connected and db_manager.alerts is not None:
        try:
            res = await db_manager.alerts.find_one_and_update(
                {"id": alert_id},
                {"$set": updates},
                return_document=True,
                projection={"_id": 0}
            )
            if not res:
                raise HTTPException(status_code=404, detail="Alert incident not found.")
            return AlertResponse(**res)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error acknowledging alert: {str(e)}")

    alerts = db_manager.memory_store.get("alerts", [])
    for a in alerts:
        if a.get("id") == alert_id:
            a.update(updates)
            return AlertResponse(**a)

    raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found.")


@router.post("/{alert_id}/resolve", response_model=AlertResponse, summary="Resolve Alert Incident")
async def resolve_alert(
    alert_id: str,
    res_req: Optional[AlertResolveRequest] = None,
    current_user: Optional[dict] = Depends(get_optional_current_user),
):
    """Mark an environmental alert as resolved with mitigation audit notes."""
    operator_name = current_user.get("username") if current_user else "Environmental Specialist"
    res_time = get_current_utc_iso()
    notes = res_req.resolution_notes if res_req else "Incident stabilized and verified compliant."

    updates = {
        "status": "Resolved",
        "resolved_at": res_time,
        "resolved_by": operator_name,
        "resolution_notes": notes,
    }

    if db_manager.is_connected and db_manager.alerts is not None:
        try:
            res = await db_manager.alerts.find_one_and_update(
                {"id": alert_id},
                {"$set": updates},
                return_document=True,
                projection={"_id": 0}
            )
            if not res:
                raise HTTPException(status_code=404, detail="Alert incident not found.")
            return AlertResponse(**res)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database error resolving alert: {str(e)}")

    alerts = db_manager.memory_store.get("alerts", [])
    for a in alerts:
        if a.get("id") == alert_id:
            a.update(updates)
            return AlertResponse(**a)

    raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found.")


@router.post("/evaluate-reading", response_model=List[AlertResponse], summary="Evaluate Telemetry against Thresholds")
async def evaluate_reading_thresholds(reading_data: Dict[str, Any]):
    """
    Check telemetry reading values against configured alert thresholds.
    Triggers new alerts if values breach warning or critical limits, with duplicate prevention.
    """
    thresholds = await get_stored_thresholds()
    location_id = reading_data.get("location_id", "station-alpha")
    loc_name = resolve_station_name(location_id)
    created_alerts = []

    # Map of metric keys to names and values in reading
    checks = [
        ("pm25", "PM2.5", reading_data.get("pm25")),
        ("pm10", "PM10", reading_data.get("pm10")),
        ("aqi", "AQI", reading_data.get("aqi")),
        ("co2", "CO2", reading_data.get("co2")),
        ("temperature", "Temperature", reading_data.get("temperature")),
        ("humidity", "Humidity", reading_data.get("humidity")),
    ]

    for key, metric_label, val in checks:
        if val is None or key not in thresholds:
            continue
        try:
            num_val = float(val)
        except (ValueError, TypeError):
            continue

        thresh_spec = thresholds[key]
        crit_val = float(thresh_spec.get("critical", 9999))
        warn_val = float(thresh_spec.get("warning", 9999))
        unit = thresh_spec.get("unit", "")

        severity = None
        limit_val = None
        if num_val >= crit_val:
            severity = "critical"
            limit_val = crit_val
        elif num_val >= warn_val:
            severity = "warning"
            limit_val = warn_val

        if severity:
            alert_in = AlertCreate(
                location_id=location_id,
                title=f"Elevated {metric_label} Level Detected",
                severity=severity,
                metric_name=metric_label,
                metric_value=f"{num_val} {unit}",
                threshold_description=f"Exceeded {severity} threshold limit of {limit_val} {unit}",
                status="Active"
            )
            # Use create_alert route function for duplicate check & persistence
            created = await create_alert(alert_in)
            created_alerts.append(created)

    return created_alerts
