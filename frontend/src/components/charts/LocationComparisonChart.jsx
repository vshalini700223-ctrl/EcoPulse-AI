import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';

const CustomLocationTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-forest-950/90 border border-emerald-500/30 p-3 rounded-xl shadow-xl backdrop-blur-md text-xs">
        <p className="font-semibold text-slate-200 mb-1">{label}</p>
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

export const LocationComparisonChart = ({ data }) => {
  return (
    <div className="eco-card p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-semibold text-white">
            Cross-Station Environmental Comparison
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Comparative analysis of AQI and PM2.5 across regional monitoring nodes
          </p>
        </div>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(20, 81, 63, 0.4)" vertical={false} />
            <XAxis dataKey="station" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <Tooltip content={<CustomLocationTooltip />} />
            <Bar dataKey="aqi" name="AQI" fill="#10b981" radius={[6, 6, 0, 0]} maxBarSize={32} />
            <Bar dataKey="pm25" name="PM2.5" fill="#2dd4bf" radius={[6, 6, 0, 0]} maxBarSize={32} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-3 pt-3 border-t border-forest-800/80 flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500" />
            AQI Score
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-teal-400" />
            PM2.5 Concentration
          </span>
        </div>
        <span className="text-[11px] text-slate-400">5 Distinct Ecological Micro-Zones</span>
      </div>
    </div>
  );
};
