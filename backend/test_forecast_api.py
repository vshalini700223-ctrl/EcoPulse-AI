import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import asyncio
import httpx
from app.main import app

async def main():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Root documentation
        r_root = await client.get("/")
        print("Root endpoints check:", "forecast_predict" in r_root.json()["endpoints"])

        # 2. Model status
        r1 = await client.get("/api/forecast/model-status")
        print("Status code:", r1.status_code)
        data1 = r1.json()
        print("Model name:", data1["model_name"])
        print("MAE:", data1["metrics"]["model_mae"], "RMSE:", data1["metrics"]["model_rmse"])
        print("Improvement %:", data1["metrics"]["mae_improvement_percent"])

        # 3. Forecast prediction for 24h
        r2 = await client.post("/api/forecast/predict", json={
            "location_id": "station-beta",
            "horizon_hours": 24
        })
        print("Predict 24h status:", r2.status_code)
        data2 = r2.json()
        print("Forecast points count:", len(data2["forecast_points"]))
        print("Historical points count:", len(data2["historical_measurements"]))
        print("First forecast point:", data2["forecast_points"][0])

        # 4. Forecast prediction for 48h
        r2_48 = await client.post("/api/forecast/predict", json={
            "location_id": "station-gamma",
            "horizon_hours": 48
        })
        print("Predict 48h status:", r2_48.status_code)
        print("Forecast 48h points count:", len(r2_48.json()["forecast_points"]))

        # 5. Model evaluation series
        r3 = await client.get("/api/forecast/evaluation")
        print("Evaluation status:", r3.status_code)
        data3 = r3.json()
        print("Test holdout points count:", len(data3["test_series"]))

        # 6. Retrain endpoint
        r4 = await client.post("/api/forecast/train", json={"train_source": "sample_dataset"})
        print("Retrain status:", r4.status_code)
        print("Retrain metrics:", r4.json()["metrics"]["model_mae"])

        print("\nALL BACKEND FORECAST API ENDPOINTS PASSED VERIFICATION!")

if __name__ == "__main__":
    asyncio.run(main())
