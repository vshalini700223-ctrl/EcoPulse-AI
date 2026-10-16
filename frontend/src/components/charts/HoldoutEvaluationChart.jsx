import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';

const CustomEvalTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const dataPoint = payload[0]?.payload;
    const actual = dataPoint.actual_pm25;
    const predicted = dataPoint.predicted_pm25;
    const error = actual != null && predicted != null ? Math.abs(actual - predicted).toFixed(1) : null;

    return (
      <div className="bg-forest-950/95 border border-forest-700/80 p-3 rounded-xl shadow-2xl backdrop-blur-md text-xs min-w-[210px]">
        <div className="text-slate-300 font-semibold mb-2 pb-1 border-b border-forest-800">
          Timestamp: {dataPoint.formattedTime || label}
        </div>
        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-emerald-400 font-medium">Actual Test Value:</span>
            <span className="font-bold text-white">{actual} µg/m³</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sky-300 font-medium">ML Regressor:</span>
            <span className="font-bold text-white">{predicted} µg/m³</span>
          </div>
          {dataPoint.baseline_persistence != null && (
            <div className="flex items-center justify-between text-amber-300/80">
              <span>Naive Baseline:</span>
              <span className="font-mono">{dataPoint.baseline_persistence} µg/m³</span>
            </div>
          )}
          {error && (
            <div className="flex items-center justify-between pt-1 border-t border-forest-800/80 text-[11px]">
              <span className="text-slate-400">Absolute Error (|y - ŷ|):</span>
              <span className="text-teal-300 font-mono font-bold">{error} µg/m³</span>
            </div>
          )}
        </div>
      </div>
    );
  }
  return null;
};

export const HoldoutEvaluationChart = ({ testSeries = [], modelName = "GradientBoostingRegressor" }) => {
  const formattedData = testSeries.map((item) => {
    let formattedTime = item.timestamp;
    try {
      const d = new Date(item.timestamp);
      formattedTime = `${d.getUTCMonth() + 1}/${d.getUTCDate()} ${String(d.getUTCHours()).padStart(2, '0')}:00`;
    } catch {
      // keep raw
    }
    return {
      ...item,
      formattedTime,
    };
  });

  return (
    <div className="eco-card p-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            Chronological Holdout Validation (Test Set Evaluation)
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Evaluated strictly on future holdout observations with zero lookahead bias
          </p>
        </div>
        <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2.5 py-1 rounded-full">
          20% Chronological Test Split
        </span>
      </div>

      <div className="h-72 sm:h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={formattedData} margin={{ top: 10, right: 20, left: -10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#064e3b" opacity={0.3} />
            <XAxis dataKey="formattedTime" stroke="#64748b" fontSize={11} tickLine={false} interval="preserveStartEnd" />
            <YAxis stroke="#64748b" fontSize={11} tickLine={false} unit=" µg" />
            <Tooltip content={<CustomEvalTooltip />} />
            <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} iconType="circle" />

            <Line
              type="monotone"
              dataKey="actual_pm25"
              name="Actual Ground Truth (Holdout)"
              stroke="#10B981"
              strokeWidth={2}
              dot={{ r: 2, fill: "#10B981" }}
            />
            <Line
              type="monotone"
              dataKey="predicted_pm25"
              name={`Model Predictions (${modelName})`}
              stroke="#38BDF8"
              strokeWidth={2}
              strokeDasharray="4 4"
              dot={{ r: 2, fill: "#38BDF8" }}
            />
            <Line
              type="monotone"
              dataKey="baseline_persistence"
              name="Naive Persistence Baseline"
              stroke="#f59e0b"
              strokeWidth={1.5}
              strokeDasharray="2 2"
              dot={false}
              opacity={0.6}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-3 flex items-center justify-between text-xs text-slate-400 border-t border-forest-800/80 pt-3">
        <span>Proof of Generalization on Unseen Holdout Data</span>
        <span className="font-mono text-[11px] text-slate-500">
          Evaluated via Mean Absolute Error (MAE) & Root Mean Squared Error (RMSE)
        </span>
      </div>
    </div>
  );
};
