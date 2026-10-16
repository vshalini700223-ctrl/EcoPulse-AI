# EcoPulse AI: Cloud-Based Environmental Monitoring, Analytics & Prediction Platform

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![MongoDB Atlas](https://img.shields.io/badge/Database-MongoDB%20Atlas-47A248.svg?style=flat&logo=mongodb)](https://www.mongodb.com/atlas)
[![React](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB.svg?style=flat&logo=react)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind%20CSS-38B2AC.svg?style=flat&logo=tailwind-css)](https://tailwindcss.com/)
[![Recharts](https://img.shields.io/badge/Charts-Recharts-22c55e.svg?style=flat)](https://recharts.org/)

EcoPulse AI is an enterprise-grade cloud environmental monitoring, telemetry analytics, and air quality predictive platform. It integrates IoT ground telemetry, satellite earth observation feeds, and machine learning forecasting models.

---

## 📁 Repository Structure

```text
EcoPulse-AI/
├── frontend/                     # React + Vite client application
│   ├── public/                   # Static assets & svg favicon
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/           # MetricCard, StatusBadge, StateHandler, SVG Icons
│   │   │   ├── layout/           # Sidebar (8 tabs), TopNav, BackendStatusBanner
│   │   │   ├── charts/           # AqiTrendChart, TempHumidityChart, LocationComparisonChart
│   │   │   └── views/            # Overview, LiveMonitoring, EnvironmentalMap, etc.
│   │   ├── data/                 # Realistic telemetry dataset & station registry
│   │   ├── services/             # Frontend API service layer (api.js)
│   │   ├── App.jsx               # Master application container with view router
│   │   ├── index.css             # Tailwind directives & deep forest styling
│   │   └── main.jsx              # React DOM entrypoint
│   ├── index.html                # HTML entrypoint with Inter typography
│   ├── package.json              # Frontend scripts & dependencies
│   ├── tailwind.config.js        # Forest & emerald custom theme palette
│   └── vite.config.js            # Dev server & /api proxy configuration
├── backend/                      # Python FastAPI service with MongoDB Atlas
│   ├── app/
│   │   ├── models/               # Pydantic v2 data validation schemas
│   │   │   ├── location.py       # Location schemas (LocationCreate, LocationResponse)
│   │   │   ├── reading.py        # Telemetry & pagination schemas (ReadingCreate, PaginatedReadingsResponse)
│   │   │   ├── alert.py          # Incident alert schemas (AlertCreate, AlertResponse)
│   │   │   ├── prediction.py     # AI prediction schemas (PredictionCreate, PredictionResponse)
│   │   │   ├── user.py           # User access schemas (UserCreate, UserResponse)
│   │   │   ├── analytics.py      # Aggregated KPIs (AnalyticsSummaryResponse)
│   │   │   └── common.py         # UUID generator & EPA AQI category classification
│   │   ├── routes/               # Modular API endpoint routers
│   │   │   ├── health.py         # GET /api/health
│   │   │   ├── locations.py      # GET /api/locations, POST /api/locations
│   │   │   ├── readings.py       # GET /api/readings, POST /api/readings
│   │   │   ├── alerts.py         # GET /api/alerts, POST /api/alerts
│   │   │   ├── analytics.py      # GET /api/analytics/summary
│   │   │   └── seed.py           # POST /api/seed
│   │   ├── services/
│   │   │   ├── database.py       # Async Motor client manager with error handling & fallback
│   │   │   └── seed_data.py      # Realistic fixtures for all 5 collections
│   │   ├── config.py             # Pydantic-settings environment configuration
│   │   └── main.py               # FastAPI app, lifespan database hooks, and CORS
│   ├── requirements.txt          # Python dependencies (FastAPI, Motor, Pydantic, etc.)
│   ├── test_api.py               # Complete automated API test suite
│   └── .env.example              # Environment variables template
├── .gitignore                    # Version control exclusion rules
└── README.md                     # Platform architecture & run guide
```

---

## 🍃 Database Architecture: MongoDB Atlas

The platform uses **MongoDB Atlas** as its document store with 5 dedicated collections:

| Collection Name | Purpose | Primary Fields |
|---|---|---|
| `users` | User credentials, roles & permissions | `id`, `username`, `email`, `role`, `is_active`, `created_at` |
| `monitoring_locations` | Ground telemetry stations & geographic metadata | `id`, `name`, `zone`, `location_type`, `latitude`, `longitude`, `status`, `active_sensors` |
| `environmental_readings` | Real-time continuous sensor readings | `id`, `location_id`, `pm25`, `pm10`, `aqi`, `aqi_category`, `temperature`, `humidity`, `co2`, `no2`, `o3`, `recorded_at` |
| `alerts` | Incident logs & threshold violation events | `id`, `location_id`, `title`, `severity`, `metric_name`, `metric_value`, `status`, `created_at` |
| `prediction_results` | Scikit-learn forecast trajectories | `id`, `location_id`, `horizon_hours`, `predicted_aqi`, `confidence_score`, `model_version`, `anomaly_risk` |

---

## ⚡ MongoDB Atlas Configuration Guide

### 1. Create a Free MongoDB Atlas Cluster
1. Sign up or log into [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).
2. Create a free shared cluster (M0 sandbox).
3. Under **Security → Database Access**, create a database user with read and write permissions (e.g. `ecopulse_admin`).
4. Under **Security → Network Access**, add your current IP address (or `0.0.0.0/0` for initial development).
5. In your cluster dashboard, click **Connect → Drivers → Python** and copy the connection string.

### 2. Configure Backend Environment
In the `backend/` directory, copy the template and configure your connection string:
```bash
cp backend/.env.example backend/.env
```
Edit `backend/.env`:
```env
ENVIRONMENT=development
PORT=8000
HOST=127.0.0.1
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Replace with your actual credentials
MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=ecopulse_ai
```

> **Safety Notice:** If `MONGODB_URI` is omitted or contains default `<username>` placeholders, the backend operates in **Safe Telemetry Fallback Mode** with in-memory stores. The server will never crash due to network or credential errors.

---

## 🔌 API Reference & Endpoints

Interactive Swagger documentation is automatically hosted at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 1. Health & Database Status
- **`GET /api/health`**
  - Returns backend operational state, MongoDB Atlas cluster connection status, and list of verified collections.

### 2. Monitoring Locations
- **`GET /api/locations`**
  - Query parameters: `status` (Optional, e.g. `Active`, `Maintenance`).
  - Returns array of all configured sensor stations.
- **`POST /api/locations`** (HTTP 201)
  - Registers a new station.
  - Body:
    ```json
    {
      "name": "EcoStation Highland Ridge",
      "zone": "Mountain Biosphere",
      "location_type": "Highland",
      "latitude": 13.1205,
      "longitude": 77.8104,
      "status": "Active",
      "active_sensors": 10,
      "total_sensors": 10
    }
    ```

### 3. Environmental Telemetry Readings
- **`GET /api/readings`**
  - Query parameters:
    - `location_id` (e.g. `station-alpha`)
    - `start_date` / `end_date` (ISO 8601 strings)
    - `page` (default: 1)
    - `limit` (default: 20, max: 100)
  - Returns paginated response: `{ total, page, limit, total_pages, items: [...] }`.
- **`POST /api/readings`** (HTTP 201)
  - Ingests a new sensor reading. Automatically calculates EPA AQI classification category (`Good`, `Moderate`, `Unhealthy`, etc.) if not specified.
  - Body:
    ```json
    {
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
    ```

### 4. Smart Alerts
- **`GET /api/alerts`**
  - Query parameters: `status` (`Active`, `Acknowledged`, `Resolved`), `severity` (`critical`, `warning`, `info`), `location_id`.
- **`POST /api/alerts`** (HTTP 201)
  - Triggers an incident alert.
  - Body:
    ```json
    {
      "location_id": "station-beta",
      "title": "High Thermal Inversion Detected",
      "severity": "warning",
      "metric_name": "Inversion Trapping",
      "metric_value": "82% Probability",
      "threshold_description": "Exceeds 70% risk threshold",
      "status": "Active"
    }
    ```

### 5. Analytics & Aggregations
- **`GET /api/analytics/summary`**
  - Returns network-wide aggregated KPIs: average AQI, peak AQI, mean PM2.5/PM10, temperature, humidity, active alert count, and overall environmental health grade (`Grade A`, `Grade B`).

### 6. Sample Data Seeding
- **`POST /api/seed`** (HTTP 201)
  - Populates all 5 collections in MongoDB Atlas (or in-memory store) with realistic station telemetry fixtures.

---

## 🏃 Running the Project Locally

### 1. Run the FastAPI Backend
```bash
cd backend

# Create & activate virtual environment (Windows PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt

# Run automated endpoint test suite
python test_api.py

# Start live FastAPI server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- API Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Check: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

### 2. Run the React Frontend
```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
- Web Application: [http://localhost:5173](http://localhost:5173)

---

## 🧪 Automated Test Verification

To execute the backend test suite:
```powershell
cd d:\EcoPulse-AI\backend
.\venv\Scripts\python test_api.py
```
All endpoints will run against the test client and output verification logs.
