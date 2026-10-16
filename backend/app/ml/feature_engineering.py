"""Feature engineering for EcoPulse AI time-series pollution forecasting.

Generates cyclical time features, backward lag features, and rolling window metrics
strictly on prior historical time steps to eliminate lookahead bias / data leakage.
"""

import os
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import math
from typing import List, Dict, Any, Tuple
import numpy as np
from app.ml.data_loader import EnvironmentalRecord

FEATURE_NAMES = [
    "sin_hour",
    "cos_hour",
    "sin_dow",
    "cos_dow",
    "is_weekend",
    "temperature",
    "humidity",
    "pm10_lag_1",
    "pm25_lag_1",
    "pm25_lag_2",
    "pm25_lag_3",
    "pm25_lag_6",
    "pm25_lag_12",
    "pm25_lag_24",
    "pm25_roll_mean_6h",
    "pm25_roll_std_6h",
    "pm25_roll_mean_24h",
]


class FeatureEngineer:
    """Constructs chronological ML feature matrices from validated environmental records."""

    @staticmethod
    def extract_time_features(dt) -> Dict[str, float]:
        """Extract cyclical trigonometric and calendar features for a given datetime."""
        hour = dt.hour + (dt.minute / 60.0)
        dow = dt.weekday()
        is_weekend = 1.0 if dow >= 5 else 0.0

        sin_hour = math.sin(2.0 * math.pi * hour / 24.0)
        cos_hour = math.cos(2.0 * math.pi * hour / 24.0)
        sin_dow = math.sin(2.0 * math.pi * dow / 7.0)
        cos_dow = math.cos(2.0 * math.pi * dow / 7.0)

        return {
            "sin_hour": round(sin_hour, 4),
            "cos_hour": round(cos_hour, 4),
            "sin_dow": round(sin_dow, 4),
            "cos_dow": round(cos_dow, 4),
            "is_weekend": is_weekend,
        }

    @classmethod
    def build_feature_dataset(
        cls,
        records: List[EnvironmentalRecord],
        target_horizon_steps: int = 1,
    ) -> Tuple[np.ndarray, np.ndarray, List[Dict[str, Any]], List[str]]:
        """Transforms a chronological series of EnvironmentalRecords into (X, y, metadata, feature_names).
        
        Args:
            records: Chronologically sorted list of EnvironmentalRecord for a station.
            target_horizon_steps: Number of hours forward for target variable (default 1 step).
            
        Returns:
            X: 2D numpy array of shape (N_samples, N_features).
            y: 1D numpy array of target PM2.5 values at t + target_horizon_steps.
            meta: Metadata per row (timestamp, location_id, actual_t, baseline_persistence).
            feature_names: List of string feature names.
        """
        # Ensure chronological sort
        sorted_records = sorted(records, key=lambda r: r.timestamp)
        n = len(sorted_records)
        
        # Need at least 25 records to construct a 24h lag + 1 step target
        min_history_required = 25
        if n < min_history_required + target_horizon_steps:
            raise ValueError(
                f"Insufficient time-series history ({n} records). "
                f"At least {min_history_required + target_horizon_steps} continuous observations required."
            )

        X_rows = []
        y_targets = []
        meta_rows = []

        # Loop from index 24 up to n - target_horizon_steps
        for i in range(24, n - target_horizon_steps):
            curr_record = sorted_records[i]
            target_idx = i + target_horizon_steps
            target_record = sorted_records[target_idx]

            # Time features at prediction target time
            time_feats = cls.extract_time_features(target_record.timestamp)

            # Lags relative to current time step i (strictly t, t-1, ...)
            pm25_l1 = sorted_records[i].pm25
            pm25_l2 = sorted_records[i - 1].pm25
            pm25_l3 = sorted_records[i - 2].pm25
            pm25_l6 = sorted_records[i - 5].pm25
            pm25_l12 = sorted_records[i - 11].pm25
            pm25_l24 = sorted_records[i - 23].pm25

            # Rolling stats over strictly past windows (i-5 to i, and i-23 to i)
            past_6_vals = [sorted_records[k].pm25 for k in range(i - 5, i + 1)]
            past_24_vals = [sorted_records[k].pm25 for k in range(i - 23, i + 1)]

            roll_mean_6h = float(np.mean(past_6_vals))
            roll_std_6h = float(np.std(past_6_vals))
            roll_mean_24h = float(np.mean(past_24_vals))

            # Exogenous measurements available at current observation time i
            pm10_l1 = sorted_records[i].pm10 or (pm25_l1 * 1.5)
            temp_val = curr_record.temperature or 24.0
            hum_val = curr_record.humidity or 60.0

            feature_vec = [
                time_feats["sin_hour"],
                time_feats["cos_hour"],
                time_feats["sin_dow"],
                time_feats["cos_dow"],
                time_feats["is_weekend"],
                temp_val,
                hum_val,
                pm10_l1,
                pm25_l1,
                pm25_l2,
                pm25_l3,
                pm25_l6,
                pm25_l12,
                pm25_l24,
                roll_mean_6h,
                roll_std_6h,
                roll_mean_24h,
            ]

            X_rows.append(feature_vec)
            y_targets.append(target_record.pm25)

            # Seasonal 24h baseline: observation 24 hours prior to target_idx
            seasonal_24h_idx = max(0, target_idx - 24)
            seasonal_24h_val = sorted_records[seasonal_24h_idx].pm25

            # Metadata for evaluation and baseline comparisons
            meta_rows.append({
                "reference_time": curr_record.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "forecast_time": target_record.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "location_id": curr_record.location_id,
                "location_name": curr_record.location_name,
                "current_pm25": curr_record.pm25,
                # Persistence baseline: predict target y_{t+h} as current value y_t
                "baseline_persistence": curr_record.pm25,
                # Seasonal baseline: predict target y_{t+h} as value 24 hours prior
                "baseline_seasonal_24h": seasonal_24h_val,
            })

        return np.array(X_rows, dtype=np.float64), np.array(y_targets, dtype=np.float64), meta_rows, FEATURE_NAMES

    @classmethod
    def build_single_step_features(
        cls,
        history_records: List[EnvironmentalRecord],
        forecast_dt,
    ) -> np.ndarray:
        """Construct a single 1D feature vector for recursive multi-step forecasting."""
        if len(history_records) < 24:
            raise ValueError("Need at least 24 past records for feature generation.")

        time_feats = cls.extract_time_features(forecast_dt)

        pm25_l1 = history_records[-1].pm25
        pm25_l2 = history_records[-2].pm25
        pm25_l3 = history_records[-3].pm25
        pm25_l6 = history_records[-6].pm25
        pm25_l12 = history_records[-12].pm25
        pm25_l24 = history_records[-24].pm25

        past_6 = [r.pm25 for r in history_records[-6:]]
        past_24 = [r.pm25 for r in history_records[-24:]]

        roll_mean_6h = float(np.mean(past_6))
        roll_std_6h = float(np.std(past_6))
        roll_mean_24h = float(np.mean(past_24))

        latest = history_records[-1]
        pm10_l1 = latest.pm10 or (pm25_l1 * 1.5)
        temp_val = latest.temperature or 24.0
        hum_val = latest.humidity or 60.0

        vec = [
            time_feats["sin_hour"],
            time_feats["cos_hour"],
            time_feats["sin_dow"],
            time_feats["cos_dow"],
            time_feats["is_weekend"],
            temp_val,
            hum_val,
            pm10_l1,
            pm25_l1,
            pm25_l2,
            pm25_l3,
            pm25_l6,
            pm25_l12,
            pm25_l24,
            roll_mean_6h,
            roll_std_6h,
            roll_mean_24h,
        ]

        return np.array([vec], dtype=np.float64)
