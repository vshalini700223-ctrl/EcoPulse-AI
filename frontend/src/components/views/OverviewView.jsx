import React from 'react';
import { MetricCard } from '../common/MetricCard';
import { StatusBadge } from '../common/StatusBadge';
import {
  IconLeaf,
  IconWind,
  IconThermometer,
  IconDroplets,
  IconMapPin,
  IconAlertTriangle,
  IconRadio,
  IconDatabase,
  IconCheckCircle,
} from '../common/Icons';
import { AqiTrendChart } from '../charts/AqiTrendChart';
import { TempHumidityChart } from '../charts/TempHumidityChart';
import { LocationComparisonChart } from '../charts/LocationComparisonChart';
import { BackendStatusBanner } from '../layout/BackendStatusBanner';
import {
  HOURLY_TELEMETRY_DATA,
  LOCATION_COMPARISON_DATA,
  RECENT_ALERTS,
  DATA_SOURCES,
} from '../../data/mockData';

export const OverviewView = ({ activeStation }) => {
  return (
    <div className="space-y-6">
      {/* Backend Communication & System Health Card */}
      <BackendStatusBanner />

      {/* Top Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Monitoring Locations */}
        <MetricCard
          title="Monitoring Network"
          value={activeStation.id === 'all' ? '5 Active' : 'Station Focus'}
          unit={activeStation.id === 'all' ? '(48 Nodes)' : '(12 Nodes)'}
          icon={IconMapPin}
          subtitle={activeStation.zone}
          statusLabel="All Online"
          statusVariant="good"
        />

        {/* Current Average AQI */}
        <MetricCard
          title="Average Air Quality"
          value={activeStation.aqi}
          unit="AQI"
          icon={IconWind}
          delta={-4.2}
          deltaText="vs previous cycle"
          isPositiveGood={false}
          statusLabel={activeStation.status}
          statusVariant={activeStation.status}
        />

        {/* Temperature & Humidity */}
        <MetricCard
          title="Microclimate Temp"
          value={activeStation.temp}
          unit="°C"
          icon={IconThermometer}
          subtitle={`Humidity: ${activeStation.humidity}% RH`}
          statusLabel="Nominal"
          statusVariant="good"
        />

        {/* PM2.5 & PM10 Levels */}
        <MetricCard
          title="Particulate Density"
          value={activeStation.pm25}
          unit="µg/m³ PM2.5"
          icon={IconLeaf}
          delta={1.8}
          deltaText={`PM10: ${activeStation.pm10} µg/m³`}
          isPositiveGood={false}
          statusLabel={activeStation.pm25 < 15 ? 'Good' : activeStation.pm25 < 35 ? 'Moderate' : 'Sensitive'}
          statusVariant={activeStation.pm25 < 15 ? 'good' : activeStation.pm25 < 35 ? 'moderate' : 'warning'}
        />
      </div>

      {/* Environmental Status Banner Indicators */}
      <div className="eco-card p-4 bg-gradient-to-r from-forest-900/90 via-forest-850/80 to-forest-900/90 flex flex-wrap items-center justify-between gap-4 border-emerald-500/20">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <IconCheckCircle className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-white">
              Environmental Biosphere Index: <span className="text-emerald-400 font-bold">Grade A (Optimal Dispersion)</span>
            </h4>
            <p className="text-xs text-slate-400 mt-0.5">
              Atmospheric stability allows rapid pollutant ventilation across the telemetry perimeter.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <span className="text-xs text-slate-400 block">Sensor Reliability</span>
            <span className="text-xs font-semibold text-emerald-300">99.8% Heartbeat Pulse</span>
          </div>
          <StatusBadge variant="good" label="Telemetry Healthy" size="sm" />
        </div>
      </div>

      {/* Charts Section: Primary AQI Trend */}
      <AqiTrendChart data={HOURLY_TELEMETRY_DATA} />

      {/* Dual Grid: Climate Chart & Location Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TempHumidityChart data={HOURLY_TELEMETRY_DATA} />
        <LocationComparisonChart data={LOCATION_COMPARISON_DATA} />
      </div>

      {/* Bottom Grid: Recent Alerts & Data Sources */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Alerts */}
        <div className="eco-card p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-semibold text-white flex items-center gap-2">
                <IconAlertTriangle className="w-4 h-4 text-amber-400" />
                Recent Environmental Alerts
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Automated threshold violation notifications & sensor notices
              </p>
            </div>
            <StatusBadge variant="warning" label="4 Active" size="xs" />
          </div>

          <div className="space-y-3">
            {RECENT_ALERTS.map((alert) => (
              <div
                key={alert.id}
                className="p-3.5 rounded-xl bg-forest-900/60 border border-forest-800/80 hover:border-emerald-500/30 transition-colors flex items-start justify-between gap-3"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-white">{alert.title}</span>
                    <StatusBadge variant={alert.severity} label={alert.status} size="xs" />
                  </div>
                  <p className="text-xs text-emerald-300/80">{alert.station}</p>
                  <p className="text-[11px] text-slate-400">
                    {alert.metric} · <span className="text-slate-500">{alert.threshold}</span>
                  </p>
                </div>
                <span className="text-[11px] text-slate-400 shrink-0">{alert.timestamp}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Data Source Indicators */}
        <div className="eco-card p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-semibold text-white flex items-center gap-2">
                <IconRadio className="w-4 h-4 text-emerald-400" />
                Data Source & Telemetry Ingestion
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Multi-stream satellite, ground sensor, and database pipes
              </p>
            </div>
            <span className="text-xs text-emerald-400 font-mono">Synced</span>
          </div>

          <div className="space-y-3">
            {DATA_SOURCES.map((source, i) => (
              <div
                key={i}
                className="p-3.5 rounded-xl bg-forest-900/60 border border-forest-800/80 flex items-center justify-between gap-4"
              >
                <div className="space-y-0.5 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-white truncate">{source.name}</span>
                    <span className="text-[10px] text-emerald-400 px-1.5 py-0.2 rounded bg-emerald-500/10 border border-emerald-500/20">
                      {source.status}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 truncate">
                    {source.type} · {source.protocol}
                  </p>
                </div>

                <div className="text-right shrink-0">
                  <span className="text-xs font-medium text-slate-200 block">{source.frequency}</span>
                  <span className="text-[10px] text-slate-400">{source.latency} latency</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
