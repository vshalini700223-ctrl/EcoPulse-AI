import React, { useState } from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-forest-950/90 border border-emerald-500/30 p-3 rounded-xl shadow-xl backdrop-blur-md text-xs">
        <p className="font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400" />
          Time: {label}
        </p>
        {payload.map((item, idx) => (
          <div key={idx} className="flex items-center justify-between gap-4 py-0.5">
            <span className="text-slate-400 capitalize">{item.name}:</span>
            <span className="font-bold text-white">
              {item.value} {item.name === 'aqi' ? 'AQI' : 'µg/m³'}
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export const AqiTrendChart = ({ data }) => {
  const [activeMetric, setActiveMetric] = useState('both'); // 'aqi', 'pm', 'both'

  return (
    <div className="eco-card p-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            Air Quality & Particulate Telemetry (24h Trend)
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Hourly continuous ambient air measurements across active regional stations
          </p>
        </div>

        <div className="flex items-center gap-1 bg-forest-900/80 p-1 rounded-xl border border-emerald-500/20 text-xs">
          <button
            onClick={() => setActiveMetric('both')}
            className={`px-2.5 py-1 rounded-lg font-medium transition-colors ${
              activeMetric === 'both'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            All Metrics
          </button>
          <button
            onClick={() => setActiveMetric('aqi')}
            className={`px-2.5 py-1 rounded-lg font-medium transition-colors ${
              activeMetric === 'aqi'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            AQI Index
          </button>
          <button
            onClick={() => setActiveMetric('pm')}
            className={`px-2.5 py-1 rounded-lg font-medium transition-colors ${
              activeMetric === 'pm'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            PM2.5 / PM10
          </button>
        </div>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="aqiGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
              </linearGradient>
              <linearGradient id="pm25Grad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#2dd4bf" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#2dd4bf" stopOpacity={0.0} />
              </linearGradient>
              <linearGradient id="pm10Grad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.0} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke="rgba(20, 81, 63, 0.4)" vertical={false} />
            <XAxis dataKey="time" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <Tooltip content={<CustomTooltip />} />

            {(activeMetric === 'both' || activeMetric === 'aqi') && (
              <Area
                type="monotone"
                dataKey="aqi"
                name="aqi"
                stroke="#10b981"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#aqiGrad)"
              />
            )}

            {(activeMetric === 'both' || activeMetric === 'pm') && (
              <Area
                type="monotone"
                dataKey="pm25"
                name="pm2.5"
                stroke="#2dd4bf"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#pm25Grad)"
              />
            )}

            {(activeMetric === 'both' || activeMetric === 'pm') && (
              <Area
                type="monotone"
                dataKey="pm10"
                name="pm10"
                stroke="#f59e0b"
                strokeWidth={1.5}
                strokeDasharray="4 4"
                fillOpacity={1}
                fill="url(#pm10Grad)"
              />
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-3 pt-3 border-t border-forest-800/80 flex flex-wrap items-center justify-between text-xs text-slate-400 gap-3">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500" />
            Overall AQI
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-teal-400" />
            PM2.5 (Fine Particles)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-amber-500" />
            PM10 (Inhalable Coarse)
          </span>
        </div>
        <span className="text-[11px] text-emerald-400/80">Sensor resolution: ±0.5 µg/m³</span>
      </div>
    </div>
  );
};
