import React, { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../../services/api';
import { MONITORING_LOCATIONS as FALLBACK_LOCATIONS } from '../../data/mockData';
import { StatusBadge } from '../common/StatusBadge';
import { SourceBadge } from '../common/SourceBadge';
import {
  IconActivity,
  IconRefresh,
  IconCloud,
  IconCpu,
  IconPlay,
  IconSquare,
  IconAlertTriangle,
  IconCheckCircle,
  IconWifiOff,
} from '../common/Icons';

export const LiveMonitoringView = () => {
  const [stations, setStations] = useState([]);
  const [ingestionStatus, setIngestionStatus] = useState(null);
  const [sourceFilter, setSourceFilter] = useState('all'); // 'all', 'real', 'simulated'
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isFetchingReal, setIsFetchingReal] = useState(false);
  const [isSimulatorToggling, setIsSimulatorToggling] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [autoRefreshInterval, setAutoRefreshInterval] = useState(10); // in seconds, 0 = off
  const [realApiError, setRealApiError] = useState(null);
  const [actionNotice, setActionNotice] = useState(null);

  const timerRef = useRef(null);

  // Load telemetry data from backend APIs
  const loadData = useCallback(async (isManualRefresh = false) => {
    if (isManualRefresh) setIsRefreshing(true);
    try {
      // 1. Fetch locations and latest telemetry readings
      const [locationsRes, readingsRes, statusRes] = await Promise.allSettled([
        api.getLocations(),
        api.getReadings({ limit: 40 }),
        api.getIngestionStatus(),
      ]);

      const rawLocations = locationsRes.status === 'fulfilled' ? locationsRes.value : [];
      const readings = readingsRes.status === 'fulfilled' && readingsRes.value?.items ? readingsRes.value.items : [];
      const statusData = statusRes.status === 'fulfilled' ? statusRes.value : null;

      if (statusData) {
        setIngestionStatus(statusData);
        // Check if external API is reported down or rate limited
        if (!statusData.external_api?.is_available) {
          setRealApiError(
            statusData.external_api?.last_error ||
            (statusData.external_api?.rate_limited
              ? `External API rate limited. Retry backoff: ${statusData.external_api.rate_limit_remaining_sec}s`
              : 'External environmental API is currently unavailable.')
          );
        } else {
          setRealApiError(null);
        }
      }

      // Group latest reading per station ID
      const latestReadingMap = {};
      readings.forEach((r) => {
        if (!latestReadingMap[r.location_id]) {
          latestReadingMap[r.location_id] = r;
        }
      });

      // Merge locations with their latest telemetry
      const effectiveLocations = rawLocations.length > 0
        ? rawLocations
        : FALLBACK_LOCATIONS.filter((l) => l.id !== 'all');

      const mergedStations = effectiveLocations.map((loc) => {
        const latest = latestReadingMap[loc.id] || {};
        return {
          id: loc.id,
          name: loc.name,
          zone: loc.zone,
          type: loc.location_type || loc.type || 'Monitoring Station',
          coordinates: loc.latitude && loc.longitude ? `${loc.latitude}° N, ${loc.longitude}° E` : loc.coordinates || 'Station Coordinates',
          status: loc.status || 'Active',
          aqi: latest.aqi !== undefined ? latest.aqi : loc.current_aqi || loc.aqi || 45,
          aqi_category: latest.aqi_category || loc.current_status || 'Good',
          pm25: latest.pm25 !== undefined ? latest.pm25 : loc.pm25 || 12.0,
          pm10: latest.pm10 !== undefined ? latest.pm10 : loc.pm10 || 24.0,
          temp: latest.temperature !== undefined ? latest.temperature : loc.temp || 24.0,
          humidity: latest.humidity !== undefined ? latest.humidity : loc.humidity || 60.0,
          co2: latest.co2 || 410.0,
          sensorsActive: loc.active_sensors || loc.sensorsActive || 12,
          sensorsTotal: loc.total_sensors || loc.sensorsTotal || 12,
          source_type: latest.source_type || 'simulated',
          source_provider: latest.source_provider || (latest.source_type === 'real' ? 'open-meteo' : 'simulator'),
          retrieved_at: latest.retrieved_at || latest.recorded_at || loc.updated_at,
          recorded_at: latest.recorded_at || loc.updated_at,
        };
      });

      setStations(mergedStations);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err) {
      console.error('Failed to load telemetry from backend:', err);
      // Retain fallback locations if totally disconnected
      if (stations.length === 0) {
        setStations(FALLBACK_LOCATIONS.filter((l) => l.id !== 'all'));
      }
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [stations.length]);

  // Initial load
  useEffect(() => {
    loadData();
  }, [loadData]);

  // Auto-refresh interval management
  useEffect(() => {
    if (autoRefreshInterval > 0) {
      timerRef.current = setInterval(() => {
        loadData();
      }, autoRefreshInterval * 1000);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [autoRefreshInterval, loadData]);

  // Trigger Real API retrieval
  const handleFetchRealData = async () => {
    setIsFetchingReal(true);
    setActionNotice(null);
    try {
      const res = await api.fetchRealData();
      if (res.status === 'completed' || res.status === 'partial') {
        setActionNotice({
          type: 'success',
          text: `Retrieved verified live readings from ${res.provider} (${res.successful_count} stations synchronized).`,
        });
        setRealApiError(null);
      } else {
        const failureReason = res.failures?.[0]?.error || 'External weather API is currently unavailable.';
        setRealApiError(failureReason);
        setActionNotice({
          type: 'error',
          text: `Real API retrieval failed: ${failureReason}`,
        });
      }
      await loadData();
    } catch (err) {
      setRealApiError(err.message || 'Unable to contact external environmental API.');
      setActionNotice({
        type: 'error',
        text: `Real API communication error: ${err.message}`,
      });
    } finally {
      setIsFetchingReal(false);
      setTimeout(() => setActionNotice(null), 6000);
    }
  };

  // Toggle Simulator Start/Stop
  const handleToggleSimulator = async () => {
    setIsSimulatorToggling(true);
    setActionNotice(null);
    try {
      const isRunning = ingestionStatus?.simulator?.is_running;
      if (isRunning) {
        const res = await api.stopSimulator();
        setActionNotice({ type: 'info', text: res.message || 'Simulator stopped.' });
      } else {
        const res = await api.startSimulator(10);
        setActionNotice({ type: 'success', text: res.message || 'Simulator started (10s cycle).' });
      }
      await loadData();
    } catch (err) {
      setActionNotice({ type: 'error', text: `Failed to toggle simulator: ${err.message}` });
    } finally {
      setIsSimulatorToggling(false);
      setTimeout(() => setActionNotice(null), 5000);
    }
  };

  // Filtered stations list
  const filteredStations = stations.filter((s) => {
    if (sourceFilter === 'real') return s.source_type === 'real';
    if (sourceFilter === 'simulated') return s.source_type === 'simulated';
    return true;
  });

  const isSimulatorRunning = ingestionStatus?.simulator?.is_running;
  const externalApiStatus = ingestionStatus?.external_api;

  return (
    <div className="space-y-6">
      {/* Top Header & Telemetry Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-forest-950/40 p-5 rounded-2xl border border-forest-800/80 backdrop-blur-xl">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
            <h2 className="text-xl font-bold text-white tracking-tight">
              Live Environmental Station Telemetry
            </h2>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Sensorless Architecture
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time multi-sensor telemetry broadcast from verified external weather APIs and continuous simulators
          </p>
        </div>

        {/* Action Controls Toolbar */}
        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          {/* Last Updated Indicator */}
          <div className="text-right px-3 py-1.5 bg-forest-900/60 rounded-xl border border-forest-800 text-[11px] text-slate-400">
            <span className="block text-[10px] text-slate-500 uppercase tracking-wider">Last Sync</span>
            <span className="font-mono text-emerald-400 font-semibold">{lastUpdated || 'Connecting...'}</span>
          </div>

          {/* Trigger Real Data Retrieval Button */}
          <button
            onClick={handleFetchRealData}
            disabled={isFetchingReal}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/40 hover:border-emerald-500/60 rounded-xl text-xs font-semibold transition-all disabled:opacity-50 shadow-[0_0_15px_rgba(16,185,129,0.15)]"
            title="Fetch live real readings from external Open-Meteo / OpenWeather API"
          >
            <IconCloud className={`w-4 h-4 ${isFetchingReal ? 'animate-bounce text-emerald-400' : ''}`} />
            {isFetchingReal ? 'Fetching Real API...' : 'Fetch Real Data'}
          </button>

          {/* Simulator Start/Stop Button */}
          <button
            onClick={handleToggleSimulator}
            disabled={isSimulatorToggling}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all border disabled:opacity-50 ${
              isSimulatorRunning
                ? 'bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border-amber-500/40'
                : 'bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border-purple-500/40'
            }`}
            title={isSimulatorRunning ? 'Stop background simulation' : 'Start background simulation'}
          >
            {isSimulatorRunning ? (
              <>
                <IconSquare className="w-3.5 h-3.5 text-amber-400" />
                Stop Simulator
              </>
            ) : (
              <>
                <IconPlay className="w-3.5 h-3.5 text-purple-400" />
                Start Simulator
              </>
            )}
          </button>

          {/* Refresh Button */}
          <button
            onClick={() => loadData(true)}
            disabled={isRefreshing}
            className="p-2 bg-forest-900/80 hover:bg-forest-800 text-slate-300 hover:text-white border border-emerald-500/20 rounded-xl transition-all"
            title="Manual Telemetry Refresh"
          >
            <IconRefresh className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-emerald-400' : ''}`} />
          </button>

          {/* Auto-Refresh Frequency Selector */}
          <div className="flex items-center bg-forest-900/80 border border-forest-800 rounded-xl px-2 py-1 text-xs">
            <span className="text-[11px] text-slate-400 mr-1.5">Auto:</span>
            <select
              value={autoRefreshInterval}
              onChange={(e) => setAutoRefreshInterval(Number(e.target.value))}
              className="bg-transparent text-emerald-400 font-mono focus:outline-none cursor-pointer text-xs"
            >
              <option value="5" className="bg-forest-900 text-slate-200">5s</option>
              <option value="10" className="bg-forest-900 text-slate-200">10s</option>
              <option value="30" className="bg-forest-900 text-slate-200">30s</option>
              <option value="0" className="bg-forest-900 text-slate-200">Off</option>
            </select>
          </div>
        </div>
      </div>

      {/* Action / Notification Banner */}
      {actionNotice && (
        <div
          className={`p-3.5 rounded-xl border flex items-center gap-3 text-xs font-medium transition-all ${
            actionNotice.type === 'error'
              ? 'bg-rose-950/40 border-rose-500/40 text-rose-300'
              : actionNotice.type === 'info'
              ? 'bg-amber-950/40 border-amber-500/40 text-amber-300'
              : 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300'
          }`}
        >
          {actionNotice.type === 'error' ? (
            <IconAlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
          ) : (
            <IconCheckCircle className="w-4 h-4 shrink-0 text-emerald-400" />
          )}
          <span>{actionNotice.text}</span>
        </div>
      )}

      {/* Real Data Unavailable Notice (Prominent Warning Requirement) */}
      {realApiError && (
        <div className="bg-amber-950/30 border border-amber-500/40 p-4 rounded-2xl flex items-start gap-3 text-xs text-amber-200 backdrop-blur-md">
          <div className="p-2 rounded-xl bg-amber-500/20 text-amber-400 shrink-0">
            <IconWifiOff className="w-5 h-5" />
          </div>
          <div className="space-y-1">
            <h4 className="font-bold text-amber-300 text-sm flex items-center gap-2">
              External Real Environmental API Unavailable
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300">
                Rate-Limit or Network Interruption
              </span>
            </h4>
            <p className="text-slate-300 leading-relaxed">
              {realApiError}
            </p>
            <p className="text-[11px] text-amber-400/80 font-mono">
              Integrity Notice: The platform never substitutes simulated values while labeling them as real.
              Continuous simulated telemetry remains active for developmental inspection.
            </p>
          </div>
        </div>
      )}

      {/* Filter Tabs & Data Source Metrics */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
        <div className="flex items-center gap-1.5 bg-forest-900/60 p-1 rounded-xl border border-forest-800 text-xs">
          <button
            onClick={() => setSourceFilter('all')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
              sourceFilter === 'all'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            All Sources ({stations.length})
          </button>
          <button
            onClick={() => setSourceFilter('real')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition-all ${
              sourceFilter === 'real'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <IconCloud className="w-3.5 h-3.5 text-emerald-400" />
            Real API Only ({stations.filter((s) => s.source_type === 'real').length})
          </button>
          <button
            onClick={() => setSourceFilter('simulated')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition-all ${
              sourceFilter === 'simulated'
                ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <IconCpu className="w-3.5 h-3.5 text-purple-400" />
            Simulated Only ({stations.filter((s) => s.source_type === 'simulated').length})
          </button>
        </div>

        {/* Source Telemetry Stats */}
        {ingestionStatus?.records_by_source && (
          <div className="flex items-center gap-3 text-xs text-slate-400 font-mono">
            <span>Real: <strong className="text-emerald-400">{ingestionStatus.records_by_source.real}</strong></span>
            <span>·</span>
            <span>Simulated: <strong className="text-purple-400">{ingestionStatus.records_by_source.simulated}</strong></span>
            <span>·</span>
            <span>Historical: <strong className="text-sky-400">{ingestionStatus.records_by_source.historical}</strong></span>
          </div>
        )}
      </div>

      {/* Monitoring Station Cards Grid */}
      {filteredStations.length === 0 ? (
        <div className="text-center py-16 eco-card space-y-3">
          <IconAlertTriangle className="w-8 h-8 text-amber-400 mx-auto" />
          <h3 className="text-base font-bold text-white">No Matching Station Telemetry</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            {sourceFilter === 'real'
              ? 'No real API readings have been ingested yet. Click "Fetch Real Data" above to query external meteorological feeds.'
              : 'No stations match the selected filter criteria.'}
          </p>
          {sourceFilter === 'real' && (
            <button
              onClick={handleFetchRealData}
              className="mt-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-semibold"
            >
              Fetch Live Readings Now
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredStations.map((station) => (
            <div
              key={station.id}
              className="eco-card p-5 space-y-4 hover:border-emerald-500/40 transition-all duration-300 relative overflow-hidden group"
            >
              {/* Card Header with Station Details and Badges */}
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-base font-bold text-white group-hover:text-emerald-300 transition-colors">
                      {station.name}
                    </h3>
                    <StatusBadge variant={station.status} label={station.status} size="xs" />
                    <SourceBadge
                      sourceType={station.source_type}
                      provider={station.source_provider}
                      size="xs"
                    />
                  </div>
                  <p className="text-xs text-emerald-400/80">
                    {station.zone} · {station.type}
                  </p>
                  <p className="text-[11px] text-slate-500 font-mono">
                    {station.coordinates}
                  </p>
                </div>

                {/* AQI Score Indicator */}
                <div className="text-right shrink-0">
                  <div className="flex items-baseline justify-end gap-1">
                    <span className="text-3xl font-black text-white">{station.aqi}</span>
                    <span className="text-xs text-slate-400 font-medium">AQI</span>
                  </div>
                  <span className={`text-[10px] uppercase font-bold block ${
                    station.aqi <= 50
                      ? 'text-emerald-400'
                      : station.aqi <= 100
                      ? 'text-amber-400'
                      : 'text-rose-400'
                  }`}>
                    {station.aqi_category}
                  </span>
                </div>
              </div>

              {/* Sensor Parameter Tiles */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-forest-800/80">
                <div className="bg-forest-900/70 p-2.5 rounded-xl border border-forest-800 hover:border-emerald-500/30 transition-colors">
                  <span className="text-[10px] text-slate-400 block uppercase font-medium">PM2.5</span>
                  <span className="text-sm font-bold text-teal-300">{station.pm25}</span>
                  <span className="text-[10px] text-slate-500 block">µg/m³</span>
                </div>

                <div className="bg-forest-900/70 p-2.5 rounded-xl border border-forest-800 hover:border-emerald-500/30 transition-colors">
                  <span className="text-[10px] text-slate-400 block uppercase font-medium">PM10</span>
                  <span className="text-sm font-bold text-amber-300">{station.pm10}</span>
                  <span className="text-[10px] text-slate-500 block">µg/m³</span>
                </div>

                <div className="bg-forest-900/70 p-2.5 rounded-xl border border-forest-800 hover:border-emerald-500/30 transition-colors">
                  <span className="text-[10px] text-slate-400 block uppercase font-medium">Temp</span>
                  <span className="text-sm font-bold text-emerald-300">{station.temp}°C</span>
                  <span className="text-[10px] text-slate-500 block">Ambient</span>
                </div>

                <div className="bg-forest-900/70 p-2.5 rounded-xl border border-forest-800 hover:border-emerald-500/30 transition-colors">
                  <span className="text-[10px] text-slate-400 block uppercase font-medium">Humidity</span>
                  <span className="text-sm font-bold text-sky-300">{station.humidity}%</span>
                  <span className="text-[10px] text-slate-500 block">Relative</span>
                </div>
              </div>

              {/* Footer with Operational Metrics & Timestamps */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between text-xs text-slate-400 pt-1 gap-1 border-t border-forest-800/40">
                <span className="flex items-center gap-1.5">
                  <IconActivity className="w-3.5 h-3.5 text-emerald-400" />
                  {station.sensorsActive} / {station.sensorsTotal} Online Probes
                </span>
                <span className="text-[11px] text-slate-500 font-mono truncate">
                  Recorded: {station.recorded_at ? new Date(station.recorded_at).toLocaleTimeString() : 'Recent'} · Source: {station.source_provider || station.source_type}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
