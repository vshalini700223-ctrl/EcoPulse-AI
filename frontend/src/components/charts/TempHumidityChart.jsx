import React from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';

const CustomClimateTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-forest-950/90 border border-emerald-500/30 p-3 rounded-xl shadow-xl backdrop-blur-md text-xs">
        <p className="font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-teal-400" />
          Time: {label}
        </p>
        {payload.map((item, idx) => (
          <div key={idx} className="flex items-center justify-between gap-4 py-0.5">
            <span className="text-slate-400 capitalize">{item.name}:</span>
            <span className="font-bold text-white">
              {item.value} {item.name === 'temp' ? '°C' : '%'}
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export const TempHumidityChart = ({ data }) => {
  return (
    <div className="eco-card p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-semibold text-white">
            Ambient Temperature & Humidity
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Microclimatic thermal profiles influencing particulate dispersion
          </p>
        </div>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(20, 81, 63, 0.4)" vertical={false} />
            <XAxis dataKey="time" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <YAxis
              yAxisId="left"
              stroke="#64748b"
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              domain={['dataMin - 2', 'dataMax + 2']}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              stroke="#64748b"
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              domain={[30, 90]}
            />
            <Tooltip content={<CustomClimateTooltip />} />

            <Line
              yAxisId="left"
              type="monotone"
              dataKey="temp"
              name="temp"
              stroke="#34d399"
              strokeWidth={2.5}
              dot={{ r: 3, fill: '#34d399' }}
              activeDot={{ r: 5 }}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="humidity"
              name="humidity"
              stroke="#38bdf8"
              strokeWidth={2}
              strokeDasharray="3 3"
              dot={{ r: 2.5, fill: '#38bdf8' }}
              activeDot={{ r: 5 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-3 pt-3 border-t border-forest-800/80 flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
            Temperature (°C)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-sky-400" />
            Relative Humidity (%)
          </span>
        </div>
        <span className="text-[11px] text-slate-400">Correlated with atmospheric boundary layer</span>
      </div>
    </div>
  );
};
