import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import api from '../../services/api';
import { MONITORING_LOCATIONS } from '../../data/mockData';
import {
  IconSettings,
  IconUser,
  IconLock,
  IconBell,
  IconShield,
  IconDatabase,
  IconCheckCircle,
  IconAlertTriangle,
} from '../common/Icons';

export const SettingsView = ({ onOpenAuth }) => {
  const { user, isAuthenticated, updateProfile } = useAuth();

  // Profile states
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [defaultStation, setDefaultStation] = useState(user?.default_location_id || 'station-alpha');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Notification preferences
  const [emailAlerts, setEmailAlerts] = useState(user?.notification_preferences?.email_alerts ?? true);
  const [inAppAlerts, setInAppAlerts] = useState(user?.notification_preferences?.in_app_alerts ?? true);
  const [minSeverity, setMinSeverity] = useState(user?.notification_preferences?.minimum_severity || 'warning');

  // Thresholds state
  const [thresholds, setThresholds] = useState({
    pm25: { warning: 35.0, critical: 75.0, unit: 'µg/m³' },
    pm10: { warning: 50.0, critical: 150.0, unit: 'µg/m³' },
    aqi: { warning: 100.0, critical: 200.0, unit: 'AQI' },
    co2: { warning: 800.0, critical: 1500.0, unit: 'ppm' },
    temperature: { warning: 38.0, critical: 45.0, unit: '°C' },
    humidity: { warning: 85.0, critical: 95.0, unit: '%' },
  });

  const [savingProfile, setSavingProfile] = useState(false);
  const [savingPassword, setSavingPassword] = useState(false);
  const [savingThresholds, setSavingThresholds] = useState(false);
  const [notificationMsg, setNotificationMsg] = useState(null);

  // Sync user values if user state changes
  useEffect(() => {
    if (user) {
      setFullName(user.full_name || '');
      setEmail(user.email || '');
      setDefaultStation(user.default_location_id || 'station-alpha');
      if (user.notification_preferences) {
        setEmailAlerts(user.notification_preferences.email_alerts ?? true);
        setInAppAlerts(user.notification_preferences.in_app_alerts ?? true);
        setMinSeverity(user.notification_preferences.minimum_severity || 'warning');
      }
    }
  }, [user]);

  // Load active thresholds from backend
  useEffect(() => {
    async function fetchThresholds() {
      try {
        const data = await api.getAlertThresholds();
        if (data) setThresholds(data);
      } catch (err) {
        console.warn('Could not fetch thresholds:', err);
      }
    }
    fetchThresholds();
  }, []);

  const showNotification = (text, isError = false) => {
    setNotificationMsg({ text, isError });
    setTimeout(() => setNotificationMsg(null), 4000);
  };

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    if (!isAuthenticated) {
      onOpenAuth && onOpenAuth();
      return;
    }
    setSavingProfile(true);
    try {
      await updateProfile({
        full_name: fullName,
        email: email,
        default_location_id: defaultStation,
        notification_preferences: {
          email_alerts: emailAlerts,
          in_app_alerts: inAppAlerts,
          minimum_severity: minSeverity,
          digest_frequency: 'instant',
        },
      });
      showNotification('Profile & preferences saved successfully.');
    } catch (err) {
      showNotification(`Error saving profile: ${err.message}`, true);
    } finally {
      setSavingProfile(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    if (!isAuthenticated) {
      onOpenAuth && onOpenAuth();
      return;
    }
    if (newPassword !== confirmPassword) {
      showNotification('New password and confirmation do not match.', true);
      return;
    }
    setSavingPassword(true);
    try {
      await api.changePassword(currentPassword, newPassword);
      showNotification('Account password updated successfully.');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      showNotification(`Error changing password: ${err.message}`, true);
    } finally {
      setSavingPassword(false);
    }
  };

  const handleSaveThresholds = async (e) => {
    e.preventDefault();
    setSavingThresholds(true);
    try {
      const updated = await api.updateAlertThresholds(thresholds);
      setThresholds(updated);
      showNotification('Environmental incident thresholds updated system-wide.');
    } catch (err) {
      showNotification(`Failed to update thresholds: ${err.message}`, true);
    } finally {
      setSavingThresholds(false);
    }
  };

  const handleThresholdChange = (param, level, val) => {
    const num = parseFloat(val);
    setThresholds((prev) => ({
      ...prev,
      [param]: {
        ...prev[param],
        [level]: isNaN(num) ? 0 : num,
      },
    }));
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <IconSettings className="w-5 h-5 text-emerald-400" />
          EcoPulse AI Platform & Security Settings
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          User profile identity, alert threshold boundaries, notification routing, and system parameters
        </p>
      </div>

      {/* Notification banner */}
      {notificationMsg && (
        <div
          className={`p-3 rounded-xl border text-xs flex items-center gap-2 animate-fade-in ${
            notificationMsg.isError
              ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
              : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
          }`}
        >
          {notificationMsg.isError ? (
            <IconAlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          ) : (
            <IconCheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
          )}
          <span>{notificationMsg.text}</span>
        </div>
      )}

      {/* Top Banner if not authenticated */}
      {!isAuthenticated && (
        <div className="eco-card p-4 border-amber-500/30 bg-amber-950/20 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <IconShield className="w-5 h-5 text-amber-400 shrink-0" />
            <div>
              <p className="text-xs font-semibold text-white">Unauthenticated Session</p>
              <p className="text-[11px] text-amber-300/80">
                Sign in with an EcoPulse account or use the quick test profiles to edit your user settings.
              </p>
            </div>
          </div>
          <button
            onClick={onOpenAuth}
            className="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-amber-500 text-forest-950 hover:bg-amber-400 transition-colors shrink-0"
          >
            Sign In Now
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Section 1: User Profile & Default Station */}
        <div className="eco-card p-6 space-y-5">
          <div className="flex items-center justify-between border-b border-forest-800 pb-3">
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <IconUser className="w-4 h-4 text-emerald-400" />
              User Profile & Default Station
            </h3>
            {user && (
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 uppercase">
                {user.role}
              </span>
            )}
          </div>

          <form onSubmit={handleSaveProfile} className="space-y-3.5 text-xs">
            <div>
              <label className="text-slate-400 block mb-1">Full Display Name</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Operator / Specialist Name"
                className="w-full px-3 py-2 bg-forest-900 border border-forest-700 rounded-xl text-white focus:outline-none focus:border-emerald-500/60"
              />
            </div>

            <div>
              <label className="text-slate-400 block mb-1">Email Address (Notifications)</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="analyst@ecopulse.ai"
                className="w-full px-3 py-2 bg-forest-900 border border-forest-700 rounded-xl text-white focus:outline-none focus:border-emerald-500/60"
              />
            </div>

            <div>
              <label className="text-slate-400 block mb-1">Default Monitored Station</label>
              <select
                value={defaultStation}
                onChange={(e) => setDefaultStation(e.target.value)}
                className="w-full px-3 py-2 bg-forest-900 border border-forest-700 rounded-xl text-emerald-300 focus:outline-none focus:border-emerald-500/60 cursor-pointer"
              >
                {MONITORING_LOCATIONS.map((loc) => (
                  <option key={loc.id} value={loc.id} className="bg-forest-900 text-white">
                    {loc.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Notification Preferences */}
            <div className="pt-2 border-t border-forest-800 space-y-2.5">
              <span className="text-xs font-semibold text-slate-300 block">Notification Routing</span>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={emailAlerts}
                  onChange={(e) => setEmailAlerts(e.target.checked)}
                  className="rounded text-emerald-500 focus:ring-0 bg-forest-900 border-forest-700"
                />
                <span className="text-slate-300">Dispatch Environmental Alert Emails (SMTP)</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={inAppAlerts}
                  onChange={(e) => setInAppAlerts(e.target.checked)}
                  className="rounded text-emerald-500 focus:ring-0 bg-forest-900 border-forest-700"
                />
                <span className="text-slate-300">Display In-App Banner & TopNav Pill Updates</span>
              </label>

              <div>
                <label className="text-slate-400 block mb-1">Minimum Severity Filter for Alerts</label>
                <select
                  value={minSeverity}
                  onChange={(e) => setMinSeverity(e.target.value)}
                  className="w-full px-3 py-2 bg-forest-900 border border-forest-700 rounded-xl text-slate-200 focus:outline-none focus:border-emerald-500/60 cursor-pointer"
                >
                  <option value="info">Informational, Warning & Critical (All)</option>
                  <option value="warning">Warning & Critical Only</option>
                  <option value="critical">Critical Ceilings Only</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={savingProfile}
              className="w-full mt-3 py-2 px-4 rounded-xl font-bold bg-emerald-500 text-forest-950 hover:bg-emerald-400 transition-colors shadow-md shadow-emerald-500/20"
            >
              {savingProfile ? 'Saving...' : 'Save Profile & Notification Settings'}
            </button>
          </form>
        </div>

        {/* Section 2: Account Password Management */}
        <div className="eco-card p-6 space-y-4">
          <h3 className="text-base font-semibold text-white flex items-center gap-2 border-b border-forest-800 pb-3">
            <IconLock className="w-4 h-4 text-emerald-400" />
            Security & Password Update
          </h3>

          <form onSubmit={handleChangePassword} className="space-y-3.5 text-xs">
            <div>
              <label className="text-slate-400 block mb-1">Current Password</label>
              <input
                type="password"
                required
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full px-3 py-2 bg-forest-900 border border-forest-700 rounded-xl text-white focus:outline-none focus:border-emerald-500/60"
              />
            </div>

            <div>
              <label className="text-slate-400 block mb-1">New Password</label>
              <input
                type="password"
                required
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Minimum 6 characters"
                className="w-full px-3 py-2 bg-forest-900 border border-forest-700 rounded-xl text-white focus:outline-none focus:border-emerald-500/60"
              />
            </div>

            <div>
              <label className="text-slate-400 block mb-1">Confirm New Password</label>
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Repeat new password"
                className="w-full px-3 py-2 bg-forest-900 border border-forest-700 rounded-xl text-white focus:outline-none focus:border-emerald-500/60"
              />
            </div>

            <button
              type="submit"
              disabled={savingPassword}
              className="w-full py-2 px-4 rounded-xl font-semibold bg-forest-900 border border-emerald-500/30 text-emerald-300 hover:bg-forest-800 transition-colors"
            >
              {savingPassword ? 'Updating Password...' : 'Update Password'}
            </button>
          </form>

          <div className="p-3 rounded-xl bg-forest-950/70 border border-forest-800 text-[11px] text-slate-400 space-y-1">
            <span className="font-semibold text-emerald-400 block">Security Architecture:</span>
            <p>
              EcoPulse AI enforces 12-round salted bcrypt cryptographic hashing. Plaintext passwords are never
              stored or transmitted. Sessions are authorized using stateless HMAC-SHA256 JWT tokens with automatic
              expiry.
            </p>
          </div>
        </div>

        {/* Section 3: Alert Threshold Configuration (System-Wide) */}
        <div className="eco-card p-6 space-y-4 lg:col-span-2">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-forest-800 pb-3">
            <div>
              <h3 className="text-base font-semibold text-white flex items-center gap-2">
                <IconBell className="w-4 h-4 text-emerald-400" />
                Environmental Alert Threshold Configuration
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Preset boundaries for automatic incident triggering, duplicate suppression, and severity levels
              </p>
            </div>
            <button
              onClick={handleSaveThresholds}
              disabled={savingThresholds}
              className="self-start sm:self-auto px-4 py-1.5 rounded-xl text-xs font-bold bg-emerald-500 text-forest-950 hover:bg-emerald-400 transition-colors"
            >
              {savingThresholds ? 'Saving...' : 'Apply Threshold Updates'}
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-xs">
            {/* PM2.5 */}
            <div className="p-3.5 rounded-xl bg-forest-950/60 border border-forest-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-white">Particulate Matter (PM2.5)</span>
                <span className="text-[10px] text-emerald-400 font-mono">µg/m³</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[11px] text-amber-300 block mb-0.5">Warning Ceiling</label>
                  <input
                    type="number"
                    step="0.1"
                    value={thresholds.pm25?.warning ?? 35}
                    onChange={(e) => handleThresholdChange('pm25', 'warning', e.target.value)}
                    className="w-full px-2 py-1 bg-forest-900 border border-forest-700 rounded-lg text-white font-mono"
                  />
                </div>
                <div>
                  <label className="text-[11px] text-rose-300 block mb-0.5">Critical Ceiling</label>
                  <input
                    type="number"
                    step="0.1"
                    value={thresholds.pm25?.critical ?? 75}
                    onChange={(e) => handleThresholdChange('pm25', 'critical', e.target.value)}
                    className="w-full px-2 py-1 bg-forest-900 border border-forest-700 rounded-lg text-white font-mono"
                  />
                </div>
              </div>
            </div>

            {/* PM10 */}
            <div className="p-3.5 rounded-xl bg-forest-950/60 border border-forest-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-white">Coarse Matter (PM10)</span>
                <span className="text-[10px] text-emerald-400 font-mono">µg/m³</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[11px] text-amber-300 block mb-0.5">Warning Ceiling</label>
                  <input
                    type="number"
                    step="0.1"
                    value={thresholds.pm10?.warning ?? 50}
                    onChange={(e) => handleThresholdChange('pm10', 'warning', e.target.value)}
                    className="w-full px-2 py-1 bg-forest-900 border border-forest-700 rounded-lg text-white font-mono"
                  />
                </div>
                <div>
                  <label className="text-[11px] text-rose-300 block mb-0.5">Critical Ceiling</label>
                  <input
                    type="number"
                    step="0.1"
                    value={thresholds.pm10?.critical ?? 150}
                    onChange={(e) => handleThresholdChange('pm10', 'critical', e.target.value)}
                    className="w-full px-2 py-1 bg-forest-900 border border-forest-700 rounded-lg text-white font-mono"
                  />
                </div>
              </div>
            </div>

            {/* AQI */}
            <div className="p-3.5 rounded-xl bg-forest-950/60 border border-forest-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-white">Air Quality Index (AQI)</span>
                <span className="text-[10px] text-emerald-400 font-mono">Index</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[11px] text-amber-300 block mb-0.5">Warning Level</label>
                  <input
                    type="number"
                    value={thresholds.aqi?.warning ?? 100}
                    onChange={(e) => handleThresholdChange('aqi', 'warning', e.target.value)}
                    className="w-full px-2 py-1 bg-forest-900 border border-forest-700 rounded-lg text-white font-mono"
                  />
                </div>
                <div>
                  <label className="text-[11px] text-rose-300 block mb-0.5">Critical Level</label>
                  <input
                    type="number"
                    value={thresholds.aqi?.critical ?? 200}
                    onChange={(e) => handleThresholdChange('aqi', 'critical', e.target.value)}
                    className="w-full px-2 py-1 bg-forest-900 border border-forest-700 rounded-lg text-white font-mono"
                  />
                </div>
              </div>
            </div>

            {/* CO2 */}
            <div className="p-3.5 rounded-xl bg-forest-950/60 border border-forest-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-white">Carbon Dioxide (CO2)</span>
                <span className="text-[10px] text-emerald-400 font-mono">ppm</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[11px] text-amber-300 block mb-0.5">Warning Level</label>
                  <input
                    type="number"
                    value={thresholds.co2?.warning ?? 800}
                    onChange={(e) => handleThresholdChange('co2', 'warning', e.target.value)}
                    className="w-full px-2 py-1 bg-forest-900 border border-forest-700 rounded-lg text-white font-mono"
                  />
                </div>
                <div>
                  <label className="text-[11px] text-rose-300 block mb-0.5">Critical Level</label>
                  <input
                    type="number"
                    value={thresholds.co2?.critical ?? 1500}
                    onChange={(e) => handleThresholdChange('co2', 'critical', e.target.value)}
                    className="w-full px-2 py-1 bg-forest-900 border border-forest-700 rounded-lg text-white font-mono"
                  />
                </div>
              </div>
            </div>

            {/* Temperature */}
            <div className="p-3.5 rounded-xl bg-forest-950/60 border border-forest-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-white">Temperature</span>
                <span className="text-[10px] text-emerald-400 font-mono">°C</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[11px] text-amber-300 block mb-0.5">Warning Level</label>
                  <input
                    type="number"
                    value={thresholds.temperature?.warning ?? 38}
                    onChange={(e) => handleThresholdChange('temperature', 'warning', e.target.value)}
                    className="w-full px-2 py-1 bg-forest-900 border border-forest-700 rounded-lg text-white font-mono"
                  />
                </div>
                <div>
                  <label className="text-[11px] text-rose-300 block mb-0.5">Critical Level</label>
                  <input
                    type="number"
                    value={thresholds.temperature?.critical ?? 45}
                    onChange={(e) => handleThresholdChange('temperature', 'critical', e.target.value)}
                    className="w-full px-2 py-1 bg-forest-900 border border-forest-700 rounded-lg text-white font-mono"
                  />
                </div>
              </div>
            </div>

            {/* Humidity */}
            <div className="p-3.5 rounded-xl bg-forest-950/60 border border-forest-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-white">Relative Humidity</span>
                <span className="text-[10px] text-emerald-400 font-mono">%</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[11px] text-amber-300 block mb-0.5">Warning Level</label>
                  <input
                    type="number"
                    value={thresholds.humidity?.warning ?? 85}
                    onChange={(e) => handleThresholdChange('humidity', 'warning', e.target.value)}
                    className="w-full px-2 py-1 bg-forest-900 border border-forest-700 rounded-lg text-white font-mono"
                  />
                </div>
                <div>
                  <label className="text-[11px] text-rose-300 block mb-0.5">Critical Level</label>
                  <input
                    type="number"
                    value={thresholds.humidity?.critical ?? 95}
                    onChange={(e) => handleThresholdChange('humidity', 'critical', e.target.value)}
                    className="w-full px-2 py-1 bg-forest-900 border border-forest-700 rounded-lg text-white font-mono"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
