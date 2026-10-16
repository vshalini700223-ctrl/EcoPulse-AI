import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { MONITORING_LOCATIONS } from '../../data/mockData';
import {
  IconFileText,
  IconDownload,
  IconRefresh,
  IconCheckCircle,
  IconAlertTriangle,
  IconFilter,
  IconMapPin,
} from '../common/Icons';

export const ReportsView = () => {
  const [selectedStation, setSelectedStation] = useState('all');
  const [timeRange, setTimeRange] = useState('7d');
  const [sourceType, setSourceType] = useState('all');
  const [summaryData, setSummaryData] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(null);
  const [statusMessage, setStatusMessage] = useState(null);

  // Calculate ISO dates for range
  const getDateRange = (rangeKey) => {
    const end = new Date().toISOString();
    const startDate = new Date();
    if (rangeKey === '24h') {
      startDate.setHours(startDate.getHours() - 24);
    } else if (rangeKey === '7d') {
      startDate.setDate(startDate.getDate() - 7);
    } else if (rangeKey === '30d') {
      startDate.setDate(startDate.getDate() - 30);
    }
    return { startDate: startDate.toISOString(), endDate: end };
  };

  const loadSummary = async () => {
    setLoading(true);
    const { startDate, endDate } = getDateRange(timeRange);
    try {
      const data = await api.getSummaryReport({
        locationId: selectedStation,
        sourceType: sourceType !== 'all' ? sourceType : undefined,
        startDate,
        endDate,
      });
      setSummaryData(data);
    } catch (err) {
      console.warn('Error fetching summary report:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadTemplates = async () => {
    try {
      const list = await api.getReportTemplates();
      setTemplates(list);
    } catch (err) {
      console.warn('Error fetching report templates:', err);
    }
  };

  useEffect(() => {
    loadSummary();
    loadTemplates();
  }, [selectedStation, timeRange, sourceType]);

  const handleExportReadingsCsv = async () => {
    setDownloading('readings');
    const { startDate, endDate } = getDateRange(timeRange);
    try {
      await api.downloadReadingsCsv({
        locationId: selectedStation,
        sourceType: sourceType !== 'all' ? sourceType : undefined,
        startDate,
        endDate,
      });
      showStatus('Telemetry readings CSV exported successfully.');
    } catch (err) {
      showStatus(`Export failed: ${err.message}`, true);
    } finally {
      setDownloading(null);
    }
  };

  const handleExportSummaryCsv = async () => {
    setDownloading('summary');
    const { startDate, endDate } = getDateRange(timeRange);
    try {
      await api.downloadSummaryCsv({
        locationId: selectedStation,
        sourceType: sourceType !== 'all' ? sourceType : undefined,
        startDate,
        endDate,
      });
      showStatus('Summary statistics CSV exported successfully.');
    } catch (err) {
      showStatus(`Export failed: ${err.message}`, true);
    } finally {
      setDownloading(null);
    }
  };

  const showStatus = (msg, isError = false) => {
    setStatusMessage({ text: msg, isError });
    setTimeout(() => setStatusMessage(null), 4000);
  };

  const metricsList = [
    { key: 'aqi', label: 'Air Quality Index (AQI)', unit: 'Index', format: (v) => v },
    { key: 'pm25', label: 'Particulate Matter PM2.5', unit: 'µg/m³', format: (v) => `${v} µg/m³` },
    { key: 'pm10', label: 'Particulate Matter PM10', unit: 'µg/m³', format: (v) => `${v} µg/m³` },
    { key: 'temperature', label: 'Ambient Temperature', unit: '°C', format: (v) => `${v} °C` },
    { key: 'humidity', label: 'Relative Humidity', unit: '%', format: (v) => `${v}%` },
    { key: 'co2', label: 'Carbon Dioxide CO2', unit: 'ppm', format: (v) => `${v} ppm` },
    { key: 'no2', label: 'Nitrogen Dioxide NO2', unit: 'µg/m³', format: (v) => `${v} µg/m³` },
    { key: 'o3', label: 'Ground Ozone O3', unit: 'µg/m³', format: (v) => `${v} µg/m³` },
  ];

  return (
    <div className="space-y-6">
      {/* Header and Download Interface */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <IconFileText className="w-5 h-5 text-emerald-400" />
            Environmental Compliance & Audit Reports
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Automated regulatory reporting, statistical evaluation, and historical CSV telemetry exports
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={handleExportReadingsCsv}
            disabled={downloading === 'readings'}
            className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-forest-900 border border-emerald-500/30 text-slate-200 hover:text-white hover:border-emerald-500/50 transition-all flex items-center gap-2"
          >
            <IconDownload className="w-4 h-4 text-emerald-400" />
            <span>{downloading === 'readings' ? 'Exporting CSV...' : 'Download Readings (CSV)'}</span>
          </button>

          <button
            onClick={handleExportSummaryCsv}
            disabled={downloading === 'summary'}
            className="px-4 py-2 rounded-xl text-xs font-bold bg-emerald-500 text-forest-950 hover:bg-emerald-400 transition-all shadow-md shadow-emerald-500/20 flex items-center gap-2"
          >
            <IconDownload className="w-4 h-4" />
            <span>{downloading === 'summary' ? 'Generating...' : 'Export Summary (CSV)'}</span>
          </button>
        </div>
      </div>

      {/* Status banner */}
      {statusMessage && (
        <div
          className={`p-3 rounded-xl border text-xs flex items-center gap-2 animate-fade-in ${
            statusMessage.isError
              ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
              : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
          }`}
        >
          {statusMessage.isError ? (
            <IconAlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          ) : (
            <IconCheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
          )}
          <span>{statusMessage.text}</span>
        </div>
      )}

      {/* Filter Parameters Bar */}
      <div className="eco-card p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          {/* Station selector */}
          <div className="relative">
            <span className="text-[10px] text-slate-400 block mb-1">Target Station:</span>
            <div className="relative flex items-center">
              <IconMapPin className="w-3.5 h-3.5 text-emerald-400 absolute left-2.5 pointer-events-none" />
              <select
                value={selectedStation}
                onChange={(e) => setSelectedStation(e.target.value)}
                className="pl-7 pr-8 py-1.5 bg-forest-900 border border-emerald-500/20 text-xs rounded-xl text-white focus:outline-none focus:border-emerald-500/50 cursor-pointer"
              >
                <option value="all">All Regional Stations</option>
                {MONITORING_LOCATIONS.map((loc) => (
                  <option key={loc.id} value={loc.id}>
                    {loc.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Time range */}
          <div>
            <span className="text-[10px] text-slate-400 block mb-1">Evaluation Interval:</span>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="px-3 py-1.5 bg-forest-900 border border-emerald-500/20 text-xs rounded-xl text-white focus:outline-none focus:border-emerald-500/50 cursor-pointer"
            >
              <option value="24h">Past 24 Hours</option>
              <option value="7d">Past 7 Days</option>
              <option value="30d">Past 30 Days</option>
            </select>
          </div>

          {/* Source filter */}
          <div>
            <span className="text-[10px] text-slate-400 block mb-1">Data Source Stream:</span>
            <select
              value={sourceType}
              onChange={(e) => setSourceType(e.target.value)}
              className="px-3 py-1.5 bg-forest-900 border border-emerald-500/20 text-xs rounded-xl text-white focus:outline-none focus:border-emerald-500/50 cursor-pointer"
            >
              <option value="all">All Available Sources</option>
              <option value="real_api">Real External APIs (Open-Meteo)</option>
              <option value="simulated">IoT Telemetry Simulator</option>
              <option value="historical">Historical Baseline Seed</option>
            </select>
          </div>
        </div>

        <button
          onClick={loadSummary}
          className="self-end md:self-center px-3 py-1.5 bg-forest-900 border border-emerald-500/20 hover:border-emerald-500/40 text-xs rounded-xl text-slate-300 hover:text-white transition-colors flex items-center gap-1.5"
        >
          <IconRefresh className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-emerald-400' : ''}`} />
          <span>Refresh Audit</span>
        </button>
      </div>

      {/* Summary Report Preview Panel */}
      {summaryData && (
        <div className="eco-card p-6 space-y-6 border-emerald-500/30">
          {/* Metadata banner */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-forest-800 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-white">{summaryData.title}</span>
                <span className="text-[10px] text-slate-500 font-mono">[{summaryData.report_id}]</span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Generated at:{' '}
                <span className="text-emerald-400 font-mono">
                  {new Date(summaryData.generation_timestamp).toUTCString()}
                </span>{' '}
                · Auditor: <span className="text-white font-medium">{summaryData.generated_by}</span>
              </p>
            </div>

            {/* Compliance Badge */}
            <div className="p-2.5 rounded-xl bg-forest-900/90 border border-emerald-500/30 text-right">
              <span className="text-[10px] text-slate-400 block">NAAQS Compliance Index</span>
              <span className="text-base font-bold text-emerald-300">
                {summaryData.compliance?.rate_percent}% Compliant
              </span>
              <span className="text-[10px] text-slate-500 block">
                {summaryData.total_readings} evaluated sensor readings
              </span>
            </div>
          </div>

          {/* Sources breakdown bar */}
          <div className="space-y-1.5">
            <span className="text-xs font-semibold text-slate-300 block">Telemetry Source Coverage</span>
            <div className="flex flex-wrap items-center gap-2">
              {Object.entries(summaryData.sources || {}).map(([src, count]) => (
                <div
                  key={src}
                  className="px-2.5 py-1 rounded-lg bg-forest-900/80 border border-emerald-500/20 text-[11px] text-slate-300 flex items-center gap-2 font-mono"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  <span className="capitalize">{src.replace('_', ' ')}</span>
                  <span className="text-emerald-300 font-bold">{count} pts</span>
                </div>
              ))}
            </div>
          </div>

          {/* Environmental Telemetry Statistical Table / Grid */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-200">
                Telemetry Metric Distribution (Average, Minimum, Maximum)
              </span>
              <span className="text-[11px] text-slate-400">Values calculated across selected timeframe</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {metricsList.map(({ key, label, unit }) => {
                const stat = summaryData.metrics?.[key] || { avg: 0, min: 0, max: 0, std_dev: 0 };
                return (
                  <div key={key} className="bg-forest-950/70 p-3.5 rounded-xl border border-forest-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white truncate">{label}</span>
                      <span className="text-[10px] text-emerald-400/80 font-mono">{unit}</span>
                    </div>

                    <div className="grid grid-cols-3 gap-1 pt-1 border-t border-forest-900 text-center">
                      <div>
                        <span className="text-[10px] text-slate-400 block">Avg</span>
                        <span className="text-xs font-bold text-emerald-300 font-mono">{stat.avg}</span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-400 block">Min</span>
                        <span className="text-xs font-bold text-teal-300 font-mono">{stat.min}</span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-400 block">Max</span>
                        <span className="text-xs font-bold text-amber-300 font-mono">{stat.max}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Pre-packaged Compliance Audit Reports */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-white">Pre-Packaged Regulatory & Audit Reports</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {templates.map((rep) => (
            <div
              key={rep.id}
              className="eco-card p-4 flex flex-col justify-between gap-3 hover:border-emerald-500/30 transition-all"
            >
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-xl bg-forest-800/80 border border-emerald-500/20 text-emerald-400 shrink-0">
                  <IconFileText className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-white">{rep.title}</h4>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Standard: <span className="text-emerald-300 font-medium">{rep.standard}</span>
                  </p>
                  <p className="text-[10px] text-slate-500 mt-0.5">
                    Coverage: {rep.coverage} · Interval: {rep.period}
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-forest-800/60">
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-forest-900 border border-forest-700 text-emerald-300 font-medium">
                  {rep.status}
                </span>

                <button
                  onClick={handleExportSummaryCsv}
                  className="px-3 py-1 text-xs font-semibold rounded-lg text-emerald-400 hover:text-white bg-forest-900 border border-emerald-500/20 hover:border-emerald-500/40 transition-colors flex items-center gap-1.5"
                >
                  <IconDownload className="w-3.5 h-3.5" />
                  <span>Download Audit (CSV)</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
