"""Generates a documented 30-day realistic historical environmental dataset for testing
the EcoPulse AI machine learning pipeline without requiring external databases.
"""

import math
import random
import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path

STATION_PROFILES = {
    "station-alpha": {
        "name": "EcoStation Alpha — Green Valley Forest",
        "pm25_base": 8.0,
        "pm25_var": 3.0,
        "pm10_base": 18.0,
        "temp_base": 20.0,
        "temp_var": 4.5,
        "humidity_base": 78.0,
        "humidity_var": 12.0,
        "traffic_impact": 0.2,
    },
    "station-beta": {
        "name": "EcoStation Beta — Urban Metro Central",
        "pm25_base": 32.0,
        "pm25_var": 9.0,
        "pm10_base": 65.0,
        "temp_base": 26.5,
        "temp_var": 6.0,
        "humidity_base": 55.0,
        "humidity_var": 14.0,
        "traffic_impact": 1.2,
    },
    "station-gamma": {
        "name": "EcoStation Gamma — Industrial Corridor",
        "pm25_base": 48.0,
        "pm25_var": 14.0,
        "pm10_base": 96.0,
        "temp_base": 28.0,
        "temp_var": 6.5,
        "humidity_base": 48.0,
        "humidity_var": 15.0,
        "traffic_impact": 1.0,
    },
    "station-delta": {
        "name": "EcoStation Delta — Coastal Biosphere",
        "pm25_base": 12.0,
        "pm25_var": 4.0,
        "pm10_base": 24.0,
        "temp_base": 23.0,
        "temp_var": 3.8,
        "humidity_base": 82.0,
        "humidity_var": 9.0,
        "traffic_impact": 0.4,
    },
}

def calculate_aqi_from_pm25(pm25: float) -> int:
    """Calculate US-EPA / CPCB standard PM2.5 AQI breakpoint approximation."""
    if pm25 <= 12.0:
        return int(round((50.0 / 12.0) * pm25))
    elif pm25 <= 35.4:
        return int(round(51.0 + ((100.0 - 51.0) / (35.4 - 12.1)) * (pm25 - 12.1)))
    elif pm25 <= 55.4:
        return int(round(101.0 + ((150.0 - 101.0) / (55.4 - 35.5)) * (pm25 - 35.5)))
    elif pm25 <= 150.4:
        return int(round(151.0 + ((200.0 - 151.0) / (150.4 - 55.5)) * (pm25 - 55.5)))
    elif pm25 <= 250.4:
        return int(round(201.0 + ((300.0 - 201.0) / (250.4 - 150.5)) * (pm25 - 150.5)))
    else:
        return min(500, int(round(301.0 + ((500.0 - 301.0) / (500.0 - 250.5)) * (pm25 - 250.5))))

def generate_dataset(days: int = 30, output_path: str = "sample_environmental_data.csv"):
    random.seed(42)
    end_time = datetime(2026, 10, 3, 0, 0, 0, tzinfo=timezone.utc)
    start_time = end_time - timedelta(days=days)
    
    records = []
    total_hours = days * 24

    for st_id, prof in STATION_PROFILES.items():
        curr = start_time
        prev_pm25 = prof["pm25_base"]
        
        for h in range(total_hours):
            hour_float = curr.hour + (curr.minute / 60.0)
            weekday = curr.weekday()
            is_weekend = weekday >= 5

            # Diurnal solar oscillation
            solar = math.sin((hour_float - 8.0) * math.pi / 12.0)
            
            # Commuter rush hour spike (8-10 AM and 5-8 PM on weekdays)
            rush_spike = 0.0
            if not is_weekend:
                if 7.0 <= hour_float <= 9.5:
                    rush_spike = 15.0 * prof["traffic_impact"]
                elif 17.0 <= hour_float <= 20.0:
                    rush_spike = 18.0 * prof["traffic_impact"]

            weekend_factor = 0.75 if is_weekend else 1.0
            
            # Multi-day atmospheric weather cycle (fronts moving through)
            macro_front = math.sin(h * 2 * math.pi / 96.0) * 4.0
            
            temp = prof["temp_base"] + (solar * prof["temp_var"]) + (macro_front * 0.4) + random.uniform(-0.5, 0.5)
            humidity = prof["humidity_base"] - (solar * prof["humidity_var"]) - (macro_front * 0.8) + random.uniform(-1.5, 1.5)
            humidity = max(15.0, min(98.0, humidity))

            # Autoregressive PM2.5 with noise, diurnal curve, and rush hour
            target_pm = (prof["pm25_base"] * weekend_factor) + rush_spike + (solar * 2.0) + (macro_front * 1.5)
            pm25 = (0.78 * prev_pm25) + (0.22 * target_pm) + random.gauss(0, prof["pm25_var"] * 0.25)
            pm25 = round(max(2.0, pm25), 1)
            prev_pm25 = pm25

            pm10 = round(max(pm25 * 1.3, pm25 * 1.7 + random.gauss(0, 3.0)), 1)
            aqi = calculate_aqi_from_pm25(pm25)
            co2 = round(400.0 + (pm25 * 1.2) + random.uniform(-5.0, 5.0), 1)
            no2 = round(max(3.0, (pm25 * 0.45) + random.uniform(-2.0, 2.0)), 1)
            o3 = round(max(4.0, 20.0 + (solar * 16.0) + random.uniform(-3.0, 3.0)), 1)

            records.append({
                "timestamp": curr.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "location_id": st_id,
                "location_name": prof["name"],
                "pm25": pm25,
                "pm10": pm10,
                "aqi": aqi,
                "temperature": round(temp, 1),
                "humidity": round(humidity, 1),
                "co2": co2,
                "no2": no2,
                "o3": o3,
                "source_type": "historical_sample",
            })

            curr += timedelta(hours=1)

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "timestamp", "location_id", "location_name", "pm25", "pm10", "aqi",
            "temperature", "humidity", "co2", "no2", "o3", "source_type"
        ])
        writer.writeheader()
        writer.writerows(records)

    print(f"Generated {len(records)} documented benchmark records across {len(STATION_PROFILES)} stations to {output_path}")

if __name__ == "__main__":
    generate_dataset(days=30, output_path="d:/EcoPulse-AI/backend/app/ml/data/sample_environmental_data.csv")
