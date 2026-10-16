import csv
import io
import math
import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Query, Response, HTTPException, Depends
from app.models.common import get_current_utc_iso, get_aqi_category, generate_uuid
from app.services.database import db_manager
from app.services.auth_service import get_optional_current_user

logger = logging.getLogger("ecopulse.routes.reports")

router = APIRouter(prefix="/reports", tags=["Reporting & Telemetry Export"])


def compute_metric_stats(values: List[float]) -> Dict[str, Any]:
    """Compute average, min, max, and std_dev for a list of numbers."""
    if not values:
        return {"avg": 0.0, "min": 0.0, "max": 0.0, "std_dev": 0.0, "count": 0}
    
    clean_vals = [float(v) for v in values if v is not None and not math.isnan(float(v))]
    if not clean_vals:
        return {"avg": 0.0, "min": 0.0, "max": 0.0, "std_dev": 0.0, "count": 0}

    n = len(clean_vals)
    avg = sum(clean_vals) / n
    min_val = min(clean_vals)
    max_val = max(clean_vals)

    if n > 1:
        variance = sum((x - avg) ** 2 for x in clean_vals) / (n - 1)
        std_dev = math.sqrt(variance)
    else:
        std_dev = 0.0

    return {
        "avg": round(avg, 2),
        "min": round(min_val, 2),
        "max": round(max_val, 2),
        "std_dev": round(std_dev, 2),
        "count": n,
    }


def resolve_station_name(location_id: Optional[str]) -> str:
    """Find station name or return 'All Monitored Locations'."""
    if not location_id or location_id.lower() == "all":
        return "All Monitored EcoStations"
    locations = db_manager.memory_store.get("monitoring_locations", [])
    for loc in locations:
        if loc.get("id") == location_id:
            return loc.get("name", location_id)
    return location_id


async def fetch_filtered_readings(
    location_id: Optional[str] = None,
    source_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 5000,
) -> List[Dict[str, Any]]:
    """Retrieve readings matching filters from database or memory store."""
    query = {}
    if location_id and location_id.lower() != "all":
        query["location_id"] = location_id
    if source_type and source_type.lower() != "all":
        query["source_type"] = source_type.lower()

    date_filter = {}
    if start_date:
        date_filter["$gte"] = start_date
    if end_date:
        date_filter["$lte"] = end_date
    if date_filter:
        query["recorded_at"] = date_filter

    if db_manager.is_connected and db_manager.environmental_readings is not None:
        try:
            cursor = db_manager.environmental_readings.find(query, {"_id": 0}).sort("recorded_at", -1)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.warning(f"Error querying readings in MongoDB: {e}")

    # Memory store fallback
    items = db_manager.memory_store.get("environmental_readings", [])
    filtered = []
    for r in items:
        if location_id and location_id.lower() != "all" and r.get("location_id") != location_id:
            continue
        if source_type and source_type.lower() != "all" and r.get("source_type", "").lower() != source_type.lower():
            continue
        rec_time = r.get("recorded_at", "")
        if start_date and rec_time < start_date:
            continue
        if end_date and rec_time > end_date:
            continue
        filtered.append(r)

    filtered.sort(key=lambda x: x.get("recorded_at", ""), reverse=True)
    return filtered[:limit]


async def build_summary_report(
    location_id: Optional[str] = None,
    source_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    username: Optional[str] = None,
) -> Dict[str, Any]:
    """Helper to compute aggregated environmental summary stats."""
    readings = await fetch_filtered_readings(location_id, source_type, start_date, end_date)
    timestamp = get_current_utc_iso()
    station_name = resolve_station_name(location_id)

    # Calculate metric statistics
    pm25_vals = [r.get("pm25") for r in readings if r.get("pm25") is not None]
    pm10_vals = [r.get("pm10") for r in readings if r.get("pm10") is not None]
    aqi_vals = [r.get("aqi") for r in readings if r.get("aqi") is not None]
    temp_vals = [r.get("temperature") for r in readings if r.get("temperature") is not None]
    hum_vals = [r.get("humidity") for r in readings if r.get("humidity") is not None]
    co2_vals = [r.get("co2") for r in readings if r.get("co2") is not None]
    no2_vals = [r.get("no2") for r in readings if r.get("no2") is not None]
    o3_vals = [r.get("o3") for r in readings if r.get("o3") is not None]
    so2_vals = [r.get("so2") for r in readings if r.get("so2") is not None]
    co_vals = [r.get("co") for r in readings if r.get("co") is not None]

    # Source breakdown
    source_breakdown = {}
    for r in readings:
        src = r.get("source_type") or r.get("data_source") or "telemetry_stream"
        source_breakdown[src] = source_breakdown.get(src, 0) + 1

    # AQI category breakdown
    aqi_categories = {
        "Good": 0,
        "Moderate": 0,
        "Unhealthy for Sensitive Groups": 0,
        "Unhealthy": 0,
        "Very Unhealthy": 0,
        "Hazardous": 0,
    }
    for val in aqi_vals:
        cat = get_aqi_category(int(val))
        if cat in aqi_categories:
            aqi_categories[cat] += 1

    total_count = len(readings)
    compliant_count = aqi_categories["Good"] + aqi_categories["Moderate"]
    compliance_rate = round((compliant_count / total_count * 100), 1) if total_count > 0 else 100.0

    return {
        "report_id": f"rep-{timestamp[:10].replace('-', '')}-{generate_uuid()[:6]}",
        "title": f"Environmental Telemetry Audit Summary: {station_name}",
        "generation_timestamp": timestamp,
        "generated_by": username or "EcoPulse System",
        "filters": {
            "location_id": location_id or "all",
            "location_name": station_name,
            "source_type": source_type or "all",
            "start_date": start_date or "earliest_available",
            "end_date": end_date or "latest_available",
        },
        "total_readings": total_count,
        "compliance": {
            "rate_percent": compliance_rate,
            "standard": "NAAQS / WHO Ambient Air Quality Guideline",
            "status": "Optimal" if compliance_rate >= 85 else ("Moderate" if compliance_rate >= 60 else "Attention Required"),
            "category_distribution": aqi_categories,
        },
        "sources": source_breakdown,
        "metrics": {
            "aqi": compute_metric_stats(aqi_vals),
            "pm25": compute_metric_stats(pm25_vals),
            "pm10": compute_metric_stats(pm10_vals),
            "temperature": compute_metric_stats(temp_vals),
            "humidity": compute_metric_stats(hum_vals),
            "co2": compute_metric_stats(co2_vals),
            "no2": compute_metric_stats(no2_vals),
            "o3": compute_metric_stats(o3_vals),
            "so2": compute_metric_stats(so2_vals),
            "co": compute_metric_stats(co_vals),
        },
    }


@router.get("/summary", summary="Generate Environmental Summary Report")
async def get_summary_report(
    location_id: Optional[str] = Query(None, description="Station ID or 'all'"),
    source_type: Optional[str] = Query(None, description="Source filter (real_api, simulated, historical)"),
    start_date: Optional[str] = Query(None, description="Start date ISO 8601"),
    end_date: Optional[str] = Query(None, description="End date ISO 8601"),
    current_user: Optional[dict] = Depends(get_optional_current_user),
):
    """
    Generate an environmental summary report with average, minimum, and maximum
    statistics for all telemetry metrics across the requested timeframe.
    """
    username = current_user.get("username") if current_user else "EcoPulse System"
    return await build_summary_report(location_id, source_type, start_date, end_date, username=username)


@router.get("/readings/csv", summary="Export Historical Readings as CSV")
async def export_readings_csv(
    location_id: Optional[str] = Query(None, description="Station ID or 'all'"),
    source_type: Optional[str] = Query(None, description="Source filter (real_api, simulated, historical)"),
    start_date: Optional[str] = Query(None, description="Start date ISO"),
    end_date: Optional[str] = Query(None, description="End date ISO"),
    limit: int = Query(5000, le=10000, description="Maximum rows to export"),
):
    """
    Download raw environmental sensor readings in CSV format.
    Includes timestamps, station identifiers, pollutant values, and source metadata.
    """
    readings = await fetch_filtered_readings(location_id, source_type, start_date, end_date, limit=limit)
    station_name = resolve_station_name(location_id)
    now_str = get_current_utc_iso()[:19].replace(":", "-")

    output = io.StringIO()
    writer = csv.writer(output)

    # Header metadata comments
    writer.writerow(["# EcoPulse AI - Environmental Telemetry Data Export"])
    writer.writerow([f"# Location: {station_name} [{location_id or 'all'}]"])
    writer.writerow([f"# Export Timestamp: {get_current_utc_iso()}"])
    writer.writerow([f"# Total Records: {len(readings)}"])
    writer.writerow([])

    # CSV Column Headers
    headers = [
        "recorded_at",
        "location_id",
        "location_name",
        "source_type",
        "aqi",
        "aqi_category",
        "pm25_ug_m3",
        "pm10_ug_m3",
        "temperature_c",
        "humidity_pct",
        "co2_ppm",
        "no2_ug_m3",
        "o3_ug_m3",
        "so2_ug_m3",
        "co_mg_m3",
    ]
    writer.writerow(headers)

    for r in readings:
        writer.writerow([
            r.get("recorded_at", ""),
            r.get("location_id", ""),
            r.get("location_name", ""),
            r.get("source_type") or r.get("data_source", "real_api"),
            r.get("aqi", ""),
            r.get("aqi_category", ""),
            r.get("pm25", ""),
            r.get("pm10", ""),
            r.get("temperature", ""),
            r.get("humidity", ""),
            r.get("co2", ""),
            r.get("no2", ""),
            r.get("o3", ""),
            r.get("so2", ""),
            r.get("co", ""),
        ])

    csv_content = output.getvalue()
    filename = f"ecopulse_telemetry_{location_id or 'all'}_{now_str}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )


@router.get("/summary/csv", summary="Export Summary Statistics Table as CSV")
async def export_summary_csv(
    location_id: Optional[str] = Query(None),
    source_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """Download calculated summary statistics (average, min, max, std dev) as a CSV report."""
    summary_data = await build_summary_report(location_id, source_type, start_date, end_date)
    metrics = summary_data.get("metrics", {})
    now_str = get_current_utc_iso()[:19].replace(":", "-")

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["# EcoPulse AI - Executive Environmental Summary Report"])
    writer.writerow([f"# Title: {summary_data.get('title')}"])
    writer.writerow([f"# Generated At: {summary_data.get('generation_timestamp')}"])
    writer.writerow([f"# Compliance Rate: {summary_data.get('compliance', {}).get('rate_percent')}%"])
    writer.writerow([f"# Total Sample Readings: {summary_data.get('total_readings')}"])
    writer.writerow([])

    writer.writerow(["Metric", "Average", "Minimum", "Maximum", "Standard_Deviation", "Sample_Count"])
    metric_labels = {
        "aqi": "Air Quality Index (AQI)",
        "pm25": "Particulate Matter PM2.5 (µg/m³)",
        "pm10": "Particulate Matter PM10 (µg/m³)",
        "temperature": "Ambient Temperature (°C)",
        "humidity": "Relative Humidity (%)",
        "co2": "Carbon Dioxide CO2 (ppm)",
        "no2": "Nitrogen Dioxide NO2 (µg/m³)",
        "o3": "Ozone O3 (µg/m³)",
        "so2": "Sulfur Dioxide SO2 (µg/m³)",
        "co": "Carbon Monoxide CO (mg/m³)",
    }

    for key, label in metric_labels.items():
        stats = metrics.get(key, {})
        writer.writerow([
            label,
            stats.get("avg", 0.0),
            stats.get("min", 0.0),
            stats.get("max", 0.0),
            stats.get("std_dev", 0.0),
            stats.get("count", 0),
        ])

    csv_content = output.getvalue()
    filename = f"ecopulse_summary_{location_id or 'all'}_{now_str}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )


@router.get("/templates", summary="List Available Regulatory & Compliance Report Templates")
async def list_report_templates():
    """List pre-configured audit and regulatory reporting packages."""
    return [
        {
            "id": "naaqs-audit-2026",
            "title": "National Ambient Air Quality (NAAQS) Compliance Audit",
            "period": "Past 30 Days",
            "category": "Regulatory Audit",
            "status": "Verified Compliant",
            "standard": "EPA / NAAQS Standard-40 CFR Part 50",
            "last_generated": "2026-10-03T06:00:00Z",
            "coverage": "All 5 Regional EcoStations",
        },
        {
            "id": "industrial-corridor-emissions",
            "title": "Industrial Corridor Continuous Emissions & Threshold Review",
            "period": "Current Quarter (Q3-Q4 2026)",
            "category": "Industrial Monitoring",
            "status": "Warning Active",
            "standard": "Industrial Zone Class IV Standard",
            "last_generated": "2026-10-02T18:00:00Z",
            "coverage": "EcoStation Gamma — Industrial Corridor",
        },
        {
            "id": "urban-microclimate-inventory",
            "title": "Metropolitan Microclimate & Greenhouse Gas Inventory",
            "period": "Annual Continuous",
            "category": "Climate Analytics",
            "status": "Scheduled Daily",
            "standard": "WMO / UNEP Urban Biosphere Guideline",
            "last_generated": "2026-10-03T00:00:00Z",
            "coverage": "EcoStation Beta & Epsilon",
        },
        {
            "id": "coastal-biosphere-integrity",
            "title": "Coastal Estuary & Biosphere Ecological Purity Report",
            "period": "Past 7 Days",
            "category": "Ecological Conservation",
            "status": "Pristine Status",
            "standard": "Coastal Zone Protection Act",
            "last_generated": "2026-10-03T08:30:00Z",
            "coverage": "EcoStation Delta — Coastal Biosphere",
        },
    ]
