import React, { useState, useEffect } from 'react';
import { IconCheckCircle, IconAlertTriangle, IconRefresh, IconDatabase, IconActivity } from '../common/Icons';

export const BackendStatusBanner = () => {
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [latency, setLatency] = useState(null);
  const [expanded, setExpanded] = useState(false);

  const checkBackendHealth = async () => {
    setLoading(true);
    setError(null);
    const startTime = performance.now();

    try {
      // First try relative path via Vite proxy, then direct localhost as fallback
      let res;
      try {
        res = await fetch('/api/health');
      } catch {
        res = await fetch('http://127.0.0.1:8000/api/health');
      }

      if (!res.ok) {
        throw new Error(`Server returned HTTP ${res.status}`);
      }

      const data = await res.json();
      const endTime = performance.now();
      setLatency(Math.round(endTime - startTime));
      setHealthData(data);
    } catch (err) {
      setError(err.message || 'Failed to connect to FastAPI backend');
      setHealthData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkBackendHealth();
  }, []);

  return (
    <div className="eco-card p-3.5 mb-6 border-emerald-500/20 bg-forest-900/40">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div
            className={`w-8 h-8 rounded-lg flex items-center justify-center ${
              healthData
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : error
                ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                : 'bg-forest-800 text-slate-400'
            }`}
          >
            {loading ? (
              <IconActivity className="w-4 h-4 animate-spin text-emerald-400" />
            ) : healthData ? (
              <IconCheckCircle className="w-4 h-4" />
            ) : (
              <IconAlertTriangle className="w-4 h-4" />
            )}
          </div>

          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-white">FastAPI Backend Health:</span>
              {loading ? (
                <span className="text-xs text-slate-400">Pinging /api/health...</span>
              ) : healthData ? (
                <span className="text-xs font-medium text-emerald-400 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                  Operational ({latency}ms)
                </span>
              ) : (
                <span className="text-xs font-medium text-rose-400">Offline / Disconnected</span>
              )}
            </div>

            <p className="text-[11px] text-slate-400">
              {healthData
                ? `${healthData.service} · Env: ${healthData.environment}`
                : error || 'Ensure backend server is running on port 8000'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-end sm:self-center">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-[11px] text-emerald-400 hover:text-emerald-300 font-medium px-2 py-1 rounded bg-forest-800/60 border border-forest-700/60 transition-colors"
          >
            {expanded ? 'Hide Details' : 'View Payload'}
          </button>

          <button
            onClick={checkBackendHealth}
            disabled={loading}
            className="inline-flex items-center gap-1 text-[11px] text-slate-200 hover:text-white font-medium px-2.5 py-1 rounded-lg bg-emerald-500/20 border border-emerald-500/30 hover:bg-emerald-500/30 transition-colors"
          >
            <IconRefresh className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
            Test Ping
          </button>
        </div>
      </div>

      {expanded && healthData && (
        <div className="mt-3 pt-3 border-t border-forest-800/80 text-xs">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 bg-forest-950/70 p-3 rounded-xl border border-forest-800 font-mono text-[11px]">
            <div>
              <span className="text-slate-500 block">Status & Version:</span>
              <span className="text-emerald-300">{healthData.status} ({healthData.version})</span>
            </div>
            <div>
              <span className="text-slate-500 block">Server Timestamp:</span>
              <span className="text-slate-300 truncate block">{healthData.timestamp}</span>
            </div>
            <div>
              <span className="text-slate-500 block">Database (Atlas):</span>
              <span className="text-teal-300">{healthData.database?.status || 'Configured'}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
