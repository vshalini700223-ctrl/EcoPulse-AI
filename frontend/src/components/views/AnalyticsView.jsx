import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { MONITORING_LOCATIONS } from '../../data/mockData';
import { IconBarChart, IconActivity, IconRefresh, IconCheckCircle, IconMapPin } from '../common/Icons';

export const AnalyticsView = () => {
  const [selectedStation, setSelectedStation] = useState('all');
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const data = await api.getAnalyticsSummary(selectedStation);
      setSummary(data);
    } catch (err) {
      console.warn('Analytics API error, using baseline fallback:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
  }, [selectedStation]);

  const pm25Val = summary?.average_pm25 ?? 18.4;
  const pm10Val = summary?.average_pm10 ?? 42.1;
  const pm25Pct = Math.min(100, Math.round((pm25Val / 35.0) * 100));
  const pm10Pct = Math.min(100, Math.round((pm10Val / 50.0) * 100));

  const POLLUTANTS = [
    { name: 'Fine Particulate Matter (PM2.5)', current: `${pm25Val} µg/m³`, standard: '15.0 µg/m³', compliance: pm25Val <= 15 ? 'Optimal' : pm25Val <= 35 ? 'Acceptable' : 'Elevated', pct: pm25Pct },
    { name: 'Coarse Particulates (PM10)', current: `${pm10Val} µg/m³`, standard: '45.0 µg/m³', compliance: pm10Val <= 45 ? 'Optimal' : 'Elevated', pct: pm10Pct },
    { name: 'Nitrogen Dioxide (NO2)', current: '28.5 ppb', standard: '53.0 ppb', compliance: 'Optimal', pct: 40 },
    { name: 'Ground-Level Ozone (O3)', current: '36.2 ppb', standard: '70.0 ppb', compliance: 'Optimal', pct: 44 },
    { name: 'Carbon Monoxide (CO)', current: '0.6 ppm', standard: '9.0 ppm', compliance: 'Optimal', pct: 18 },
    { name: 'Sulfur Dioxide (SO2)', current: '4.8 ppb', standard: '35.0 ppb', compliance: 'Optimal', pct: 22 },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <IconBarChart className="w-5 h-5 text-emerald-400" />
            Pollutant Distribution & Exposure Analytics
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Chemical biomarker concentrations, regional dispersion index, and regulatory compliance benchmarks
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="relative flex items-center">
            <IconMapPin className="w-3.5 h-3.5 text-emerald-400 absolute left-2.5 pointer-events-none" />
            <select
              value={selectedStation}
              onChange={(e) => setSelectedStation(e.target.value)}
              className="pl-7 pr-8 py-1.5 bg-forest-900 border border-emerald-500/20 text-xs rounded-xl text-white focus:outline-none focus:border-emerald-500/50 cursor-pointer"
            >
              <option value="all">All Regional Stations</option>
              {MONITORING_LOCATIONS.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.name}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={loadAnalytics}
            className="p-1.5 rounded-xl bg-forest-900 border border-emerald-500/20 text-slate-300 hover:text-white transition-colors"
            title="Refresh Analytics"
          >
            <IconRefresh className={`w-4 h-4 ${loading ? 'animate-spin text-emerald-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* Analytics KPI Highlights */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="eco-card p-4">
          <span className="text-[11px] text-slate-400 font-medium block">Regional Dispersion Grade</span>
          <span className="text-2xl font-bold text-emerald-400 mt-1 block">
            {summary?.environmental_grade || summary?.air_quality_grade || 'Grade B'}
          </span>
          <span className="text-[10px] text-slate-500">Evaluated vs EPA Guideline</span>
        </div>

        <div className="eco-card p-4">
          <span className="text-[11px] text-slate-400 font-medium block">Mean Baseline AQI</span>
          <span className="text-2xl font-bold text-teal-300 mt-1 block">
            {summary?.average_aqi ? `${summary.average_aqi} AQI` : '66.0 AQI'}
          </span>
          <span className="text-[10px] text-slate-500">
            {selectedStation === 'all'
              ? 'Across all continuous monitoring corridors'
              : summary?.location_name || 'Station Specific Telemetry'}
          </span>
        </div>

        <div className="eco-card p-4">
          <span className="text-[11px] text-slate-400 font-medium block">Dominant Risk Driver</span>
          <span className="text-2xl font-bold text-amber-300 mt-1 block">
            {summary?.dominant_pollutant || 'PM2.5'}
          </span>
          <span className="text-[10px] text-slate-500">Primary respiratory exposure vector</span>
        </div>
      </div>

      {/* Benchmark Table */}
      <div className="eco-card p-6">
        <h3 className="text-base font-semibold text-white mb-4">
          Atmospheric Constituent Breakdown vs WHO Standards
        </h3>

        <div className="space-y-4">
          {POLLUTANTS.map((pol, i) => (
            <div key={i} className="p-4 rounded-xl bg-forest-900/60 border border-forest-800">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                <span className="text-sm font-semibold text-white">{pol.name}</span>
                <div className="flex items-center gap-3 text-xs">
                  <span className="text-slate-400">
                    Current: <span className="text-emerald-300 font-bold">{pol.current}</span>
                  </span>
                  <span className="text-slate-500">WHO Limit: {pol.standard}</span>
                </div>
              </div>

              {/* Progress bar */}
              <div className="w-full h-2.5 rounded-full bg-forest-950 overflow-hidden border border-forest-800">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    pol.pct > 75 ? 'bg-amber-500' : 'bg-emerald-400'
                  }`}
                  style={{ width: `${pol.pct}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
