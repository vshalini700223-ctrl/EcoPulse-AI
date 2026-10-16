import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { StatusBadge } from '../common/StatusBadge';
import {
  IconBell,
  IconAlertTriangle,
  IconCheckCircle,
  IconShield,
  IconRefresh,
  IconSettings,
} from '../common/Icons';

export const SmartAlertsView = () => {
  const { user, isAuthenticated } = useAuth();
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState({ total: 0, active: 0, acknowledged: 0, resolved: 0, critical: 0, warning: 0, info: 0 });
  const [filter, setFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [actionMessage, setActionMessage] = useState(null);
  const [thresholds, setThresholds] = useState(null);
  const [showThresholdModal, setShowThresholdModal] = useState(false);
  const [resolveModalAlert, setResolveModalAlert] = useState(null);
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [triggeringTest, setTriggeringTest] = useState(false);

  // Fetch alerts and stats from backend
  const loadAlerts = async () => {
    setLoading(true);
    try {
      const [alertList, alertStats, threshData] = await Promise.all([
        api.getAlerts(),
        api.getAlertStats(),
        api.getAlertThresholds(),
      ]);
      setAlerts(alertList);
      setStats(alertStats);
      setThresholds(threshData);
    } catch (err) {
      console.warn('Backend alerts error, using fallback:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, []);

  const handleAcknowledge = async (id) => {
    try {
      const updated = await api.acknowledgeAlert(id, 'Acknowledged by operator');
      setAlerts((prev) => prev.map((a) => (a.id === id ? updated : a)));
      setStats((prev) => ({
        ...prev,
        active: Math.max(0, prev.active - 1),
        acknowledged: prev.acknowledged + 1,
      }));
      showMessage(`Incident [${id}] acknowledged successfully.`);
    } catch (err) {
      showMessage(`Failed to acknowledge: ${err.message}`, true);
    }
  };

  const handleResolve = async (e) => {
    e.preventDefault();
    if (!resolveModalAlert) return;
    try {
      const updated = await api.resolveAlert(
        resolveModalAlert.id,
        resolutionNotes || 'Incident stabilized and environmental telemetry verified normal.'
      );
      setAlerts((prev) => prev.map((a) => (a.id === resolveModalAlert.id ? updated : a)));
      setStats((prev) => ({
        ...prev,
        active: resolveModalAlert.status === 'Active' ? Math.max(0, prev.active - 1) : prev.active,
        acknowledged: resolveModalAlert.status === 'Acknowledged' ? Math.max(0, prev.acknowledged - 1) : prev.acknowledged,
        resolved: prev.resolved + 1,
      }));
      showMessage(`Incident [${resolveModalAlert.id}] marked as resolved.`);
      setResolveModalAlert(null);
      setResolutionNotes('');
    } catch (err) {
      showMessage(`Failed to resolve: ${err.message}`, true);
    }
  };

  const showMessage = (msg, isError = false) => {
    setActionMessage({ text: msg, isError });
    setTimeout(() => setActionMessage(null), 4000);
  };

  // Test Trigger Threshold Breaches & Duplicate Prevention
  const handleTriggerTestAlert = async (isCritical = true) => {
    setTriggeringTest(true);
    try {
      const testReading = isCritical
        ? {
            location_id: 'station-gamma',
            pm25: 88.5, // Exceeds critical threshold 75.0
            pm10: 160.0,
            aqi: 185,
            co2: 950.0,
            temperature: 32.0,
            humidity: 48.0,
          }
        : {
            location_id: 'station-beta',
            pm25: 42.0, // Exceeds warning threshold 35.0
            pm10: 60.0,
            aqi: 110,
            co2: 650.0,
            temperature: 28.0,
            humidity: 55.0,
          };

      const triggered = await api.evaluateReadingThresholds(testReading);
      await loadAlerts();
      showMessage(
        triggered.length > 0
          ? `Evaluated telemetry: triggered ${triggered.length} alert(s) (with automated duplicate prevention).`
          : 'Telemetry within normal limits.'
      );
    } catch (err) {
      showMessage(`Simulation error: ${err.message}`, true);
    } finally {
      setTriggeringTest(false);
    }
  };

  const filteredAlerts = alerts.filter((a) => {
    if (filter !== 'all' && a.severity !== filter) return false;
    if (statusFilter !== 'all' && a.status.toLowerCase() !== statusFilter.toLowerCase()) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <IconBell className="w-5 h-5 text-amber-400" />
            Smart Environmental Incident & Alert Hub
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Automated threshold surveillance, duplicate incident suppression, and resolution audit tracking
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Quick Trigger Button to test duplicate prevention */}
          <button
            onClick={() => handleTriggerTestAlert(true)}
            disabled={triggeringTest}
            className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/40 hover:bg-rose-500/30 transition-colors flex items-center gap-1.5"
            title="Simulate high PM2.5 spike to test threshold breach and duplicate prevention"
          >
            <IconAlertTriangle className="w-3.5 h-3.5" />
            <span>Simulate Spike (Test Deduplication)</span>
          </button>

          <button
            onClick={loadAlerts}
            className="p-1.5 rounded-xl bg-forest-900 border border-emerald-500/20 text-slate-300 hover:text-white hover:border-emerald-500/40 transition-colors"
            title="Reload Alerts"
          >
            <IconRefresh className={`w-4 h-4 ${loading ? 'animate-spin text-emerald-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* Notification banner */}
      {actionMessage && (
        <div
          className={`p-3 rounded-xl border text-xs flex items-center gap-2 animate-fade-in ${
            actionMessage.isError
              ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
              : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
          }`}
        >
          {actionMessage.isError ? (
            <IconAlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          ) : (
            <IconCheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
          )}
          <span>{actionMessage.text}</span>
        </div>
      )}

      {/* Incident Metric Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="eco-card p-4">
          <span className="text-[11px] text-slate-400 font-medium block">Total Recorded</span>
          <span className="text-2xl font-bold text-white mt-1 block">{stats.total}</span>
          <span className="text-[10px] text-slate-500">Historical telemetry log</span>
        </div>
        <div className="eco-card p-4 border-rose-500/30 bg-rose-950/10">
          <span className="text-[11px] text-rose-300 font-medium block">Active Critical / Warning</span>
          <span className="text-2xl font-bold text-rose-400 mt-1 block">{stats.active}</span>
          <span className="text-[10px] text-rose-400/80">Requires immediate attention</span>
        </div>
        <div className="eco-card p-4 border-amber-500/30 bg-amber-950/10">
          <span className="text-[11px] text-amber-300 font-medium block">Acknowledged</span>
          <span className="text-2xl font-bold text-amber-400 mt-1 block">{stats.acknowledged}</span>
          <span className="text-[10px] text-amber-400/80">Under operator inspection</span>
        </div>
        <div className="eco-card p-4 border-emerald-500/30 bg-emerald-950/10">
          <span className="text-[11px] text-emerald-300 font-medium block">Resolved</span>
          <span className="text-2xl font-bold text-emerald-400 mt-1 block">{stats.resolved}</span>
          <span className="text-[10px] text-emerald-400/80">Verified & closed</span>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-forest-950/80 p-3 rounded-2xl border border-forest-800">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-xs text-slate-400 mr-1 font-medium">Severity:</span>
          {['all', 'critical', 'warning', 'info'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-2.5 py-1 rounded-lg text-xs font-semibold capitalize transition-all ${
                filter === f
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {f}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-xs text-slate-400 mr-1 font-medium">Status:</span>
          {['all', 'Active', 'Acknowledged', 'Resolved'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-2.5 py-1 rounded-lg text-xs font-semibold capitalize transition-all ${
                statusFilter === st
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Alerts List */}
      <div className="space-y-3">
        {filteredAlerts.length === 0 ? (
          <div className="eco-card p-8 text-center text-slate-400 text-xs">
            No environmental incident alerts match the current severity and status filters.
          </div>
        ) : (
          filteredAlerts.map((alert) => (
            <div
              key={alert.id}
              className="eco-card p-5 flex flex-col lg:flex-row lg:items-center justify-between gap-4 transition-all hover:border-emerald-500/30"
            >
              <div className="flex items-start gap-3.5">
                <div
                  className={`p-2.5 rounded-xl shrink-0 ${
                    alert.severity === 'critical'
                      ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                      : alert.severity === 'warning'
                      ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                      : 'bg-teal-500/20 text-teal-400 border border-teal-500/30'
                  }`}
                >
                  <IconAlertTriangle className="w-5 h-5" />
                </div>

                <div className="space-y-1.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-bold text-white">{alert.title}</span>
                    <span className="text-[11px] text-slate-500 font-mono">[{alert.id}]</span>
                    <StatusBadge variant={alert.severity} label={alert.status} size="xs" />
                    {alert.duplicate_count > 0 && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                        Duplicate Suppressed ({alert.duplicate_count}x)
                      </span>
                    )}
                  </div>

                  <p className="text-xs text-emerald-400 font-medium">
                    {alert.location_name || alert.location_id}
                  </p>

                  <p className="text-xs text-slate-300">
                    <span className="font-semibold text-white">{alert.metric_name}:</span>{' '}
                    <span className="font-mono text-emerald-300">{alert.metric_value}</span> —{' '}
                    <span className="text-slate-400">{alert.threshold_description}</span>
                  </p>

                  {/* Audit trail details */}
                  {(alert.acknowledged_by || alert.resolved_by) && (
                    <div className="text-[11px] text-slate-400 pt-1 space-y-0.5 border-t border-forest-800/60 mt-1">
                      {alert.acknowledged_by && (
                        <p>
                          Acknowledged by <span className="text-slate-200 font-medium">{alert.acknowledged_by}</span> at{' '}
                          {new Date(alert.acknowledged_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </p>
                      )}
                      {alert.resolved_by && (
                        <p>
                          Resolved by <span className="text-slate-200 font-medium">{alert.resolved_by}</span>:{' '}
                          <span className="italic text-emerald-300">"{alert.resolution_notes}"</span>
                        </p>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 self-end lg:self-center shrink-0">
                <span className="text-[11px] text-slate-400 mr-2 font-mono">
                  {new Date(alert.created_at).toLocaleDateString([], { month: 'short', day: 'numeric' })}{' '}
                  {new Date(alert.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>

                {alert.status === 'Active' && (
                  <button
                    onClick={() => handleAcknowledge(alert.id)}
                    className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30 hover:bg-amber-500/30 transition-colors"
                  >
                    Acknowledge
                  </button>
                )}

                {alert.status !== 'Resolved' && (
                  <button
                    onClick={() => setResolveModalAlert(alert)}
                    className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/30 transition-colors"
                  >
                    Resolve Incident
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Resolve Incident Modal */}
      {resolveModalAlert && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
          <div className="bg-[#051c14] border border-emerald-500/30 w-full max-w-md rounded-2xl shadow-2xl p-6 relative">
            <h3 className="text-base font-bold text-white flex items-center gap-2 mb-2">
              <IconCheckCircle className="w-5 h-5 text-emerald-400" />
              Resolve Environmental Incident [{resolveModalAlert.id}]
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Station: <span className="text-white font-medium">{resolveModalAlert.location_name}</span> · Metric:{' '}
              <span className="text-emerald-300 font-mono">{resolveModalAlert.metric_name} ({resolveModalAlert.metric_value})</span>
            </p>

            <form onSubmit={handleResolve} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Resolution Notes & Corrective Actions
                </label>
                <textarea
                  rows={3}
                  required
                  placeholder="e.g. Scrubber filters refreshed, air circulation increased, sensor calibrated."
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  className="w-full px-3 py-2 bg-forest-900 border border-forest-700 rounded-xl text-xs text-white focus:outline-none focus:border-emerald-500/50"
                />
              </div>

              <div className="flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setResolveModalAlert(null)}
                  className="px-3.5 py-1.5 rounded-xl text-xs font-semibold text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-xl text-xs font-bold bg-emerald-500 text-forest-950 hover:bg-emerald-400 transition-colors"
                >
                  Confirm Resolution
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
