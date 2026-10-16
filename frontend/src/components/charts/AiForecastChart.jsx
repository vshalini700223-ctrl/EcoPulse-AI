import React from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  Legend,
} from 'recharts';

const CustomForecastTooltip = ({ active, payload, label, metricMode }) => {
  if (active && payload && payload.length) {
    const dataPoint = payload[0]?.payload;
    if (!dataPoint) return null;

    const isForecast = dataPoint.is_forecast;

    return (
      <div className="bg-forest-950/95 border border-forest-700/80 p-3.5 rounded-xl shadow-2xl backdrop-blur-md text-xs min-w-[220px]">
        <div className="flex items-center justify-between pb-2 mb-2 border-b border-forest-800">
          <span className="font-semibold text-slate-300 flex items-center gap-1.5">
            <span
              className={`w-2 h-2 rounded-full ${
                isForecast ? 'bg-sky-400 animate-pulse' : 'bg-emerald-400'
              }`}
            />
            {dataPoint.formattedTime || label}
          </span>
          <span
            className={`px-1.5 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider font-semibold ${
              isForecast
                ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30'
                : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
            }`}
          >
            {isForecast ? `Forecast ${dataPoint.hour_offset || ''}` : 'Actual History'}
          </span>
        </div>

        <div className="space-y-1.5">
          {metricMode === 'pm25' ? (
            <>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">PM2.5:</span>
                <span className="font-bold text-white text-sm">
                  {isForecast ? dataPoint.predicted_pm25 : dataPoint.actual_pm25} µg/m³
                </span>
              </div>
              {isForecast && (
                <div className="flex items-center justify-between text-slate-400 text-[11px]">
                  <span>95% Confidence Band:</span>
                  <span className="text-sky-300 font-mono">
                    {dataPoint.pm25_lower} – {dataPoint.pm25_upper} µg/m³
                  </span>
                </div>
              )}
            </>
          ) : (
            <>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Air Quality Index (AQI):</span>
                <span className="font-bold text-white text-sm">
                  {isForecast ? dataPoint.predicted_aqi : dataPoint.actual_aqi} AQI
                </span>
              </div>
              {dataPoint.aqi_category && (
                <div className="flex items-center justify-between text-slate-400 text-[11px]">
                  <span>Health Risk:</span>
                  <span className="text-emerald-300 font-medium">
                    {dataPoint.aqi_category}
                  </span>
                </div>
              )}
            </>
          )}

          {isForecast && dataPoint.confidence_percent && (
            <div className="flex items-center justify-between pt-1 border-t border-forest-800/80 text-[11px]">
              <span className="text-slate-400">Model Confidence:</span>
              <span className="text-teal-300 font-bold">{dataPoint.confidence_percent}</span>
            </div>
          )}
        </div>
      </div>
    );
  }
  return null;
};

export const AiForecastChart = ({
  chartData = [],
  metricMode = 'pm25', // 'pm25' or 'aqi'
  splitIndex = -1,
  chartTitle = "Atmospheric Forecast Trajectory",
  subtitle = "Continuous 24h actual readings transitioning to multi-step recursive ML predictions",
}) => {
  const isPm25 = metricMode === 'pm25';

  return (
    <div className="eco-card p-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div>
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            {chartTitle}
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>
        </div>
      </div>

      <div className="h-72 sm:h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={chartData}
            margin={{ top: 10, right: 20, left: -10, bottom: 5 }}
          >
            <defs>
              <linearGradient id="actualGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10B981" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#10B981" stopOpacity={0.0} />
              </linearGradient>
              <linearGradient id="forecastUncertainty" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#38BDF8" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#38BDF8" stopOpacity={0.05} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke="#064e3b" opacity={0.3} />

            <XAxis
              dataKey="formattedTime"
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              stroke="#64748b"
              fontSize={11}
              tickLine={false}
              domain={['auto', 'auto']}
              unit={isPm25 ? " µg" : ""}
            />

            <Tooltip
              content={<CustomForecastTooltip metricMode={metricMode} />}
            />

            <Legend
              wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }}
              iconType="circle"
            />

            {/* Shaded Uncertainty Confidence Interval Band (Forecast points only) */}
            {isPm25 && (
              <Area
                type="monotone"
                dataKey="pm25_upper"
                name="Confidence Range (+95%)"
                stroke="transparent"
                fill="url(#forecastUncertainty)"
                isAnimationActive={false}
              />
            )}

            {/* Actual Historical Telemetry Line */}
            <Line
              type="monotone"
              dataKey={isPm25 ? "actual_pm25" : "actual_aqi"}
              name={isPm25 ? "Actual PM2.5 (Historical)" : "Actual AQI (Historical)"}
              stroke="#10B981"
              strokeWidth={2.5}
              dot={{ r: 2.5, fill: "#10B981", strokeWidth: 0 }}
              activeDot={{ r: 5, fill: "#34D399" }}
              connectNulls={false}
            />

            {/* Predicted Machine Learning Forecast Line */}
            <Line
              type="monotone"
              dataKey={isPm25 ? "predicted_pm25" : "predicted_aqi"}
              name={isPm25 ? "Predicted PM2.5 (ML Forecast)" : "Predicted AQI (ML Forecast)"}
              stroke="#38BDF8"
              strokeWidth={2.5}
              strokeDasharray="5 5"
              dot={{ r: 3, fill: "#38BDF8", strokeWidth: 1, stroke: "#0369a1" }}
              activeDot={{ r: 6, fill: "#7dd3fc" }}
              connectNulls={false}
            />

            {/* Boundary marker if splitIndex provided */}
            {splitIndex >= 0 && chartData[splitIndex] && (
              <ReferenceLine
                x={chartData[splitIndex].formattedTime}
                stroke="#f59e0b"
                strokeDasharray="3 3"
                label={{
                  value: "Forecast Origin",
                  position: "insideTopLeft",
                  fill: "#f59e0b",
                  fontSize: 10,
                  fontWeight: 600,
                }}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-3 flex flex-wrap items-center justify-between text-xs text-slate-400 border-t border-forest-800/80 pt-3">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-0.5 bg-emerald-400 rounded-full" />
            Solid: Past Recorded Telemetry
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-0.5 bg-sky-400 border-b border-dashed rounded-full" />
            Dashed: Future Recursive Steps
          </span>
          {isPm25 && (
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2 bg-sky-400/20 border border-sky-400/40 rounded-sm" />
              Shaded: Uncertainty Margin (±1.96·RMSE)
            </span>
          )}
        </div>
        <span className="text-slate-500 font-mono text-[11px]">
          Chronological Autoregressive Stepping
        </span>
      </div>
    </div>
  );
};
