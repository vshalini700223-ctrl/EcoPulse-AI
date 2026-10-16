/**
 * EcoPulse AI - Frontend API Service Layer
 * Interacts with the FastAPI backend, MongoDB Atlas collections, and JWT Authentication.
 */

const getApiBaseUrl = () => {
  const envUrl = typeof import.meta !== 'undefined' && import.meta.env ? import.meta.env.VITE_API_URL : null;
  if (!envUrl) return '/api';
  const clean = envUrl.trim().replace(/\/+$/, '');
  return clean.endsWith('/api') ? clean : `${clean}/api`;
};

const BASE_URL = getApiBaseUrl();


/**
 * Retrieve active JWT token from browser storage
 */
export function getStoredToken() {
  try {
    return localStorage.getItem('ecopulse_token');
  } catch {
    return null;
  }
}

/**
 * Persist or clear JWT token in browser storage
 */
export function setStoredToken(token) {
  try {
    if (token) {
      localStorage.setItem('ecopulse_token', token);
    } else {
      localStorage.removeItem('ecopulse_token');
    }
  } catch (e) {
    console.error('Error accessing localStorage:', e);
  }
}

/**
 * Helper to fetch with JWT auth header, error handling and JSON parsing
 */
async function fetchJson(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const token = getStoredToken();
  const authHeaders = token ? { Authorization: `Bearer ${token}` } : {};

  const headers = {
    'Content-Type': 'application/json',
    ...authHeaders,
    ...options.headers,
  };

  try {
    const res = await fetch(url, {
      ...options,
      headers,
    });

    if (!res.ok) {
      const errorBody = await res.json().catch(() => ({}));
      throw new Error(errorBody.detail || `HTTP Error ${res.status}: ${res.statusText}`);
    }

    return await res.json();
  } catch (err) {
    // If proxy failed, attempt direct backend fallback on localhost
    if (err.name === 'TypeError' || err.message.includes('Failed to fetch')) {
      try {
        const directUrl = `http://127.0.0.1:8000/api${endpoint}`;
        const directRes = await fetch(directUrl, {
          ...options,
          headers,
        });
        if (directRes.ok) return await directRes.json();
      } catch {
        // Fall back to original error
      }
    }
    throw err;
  }
}

/**
 * Helper to trigger file download from binary or text responses
 */
async function downloadFile(endpoint, filenameFallback) {
  const url = `${BASE_URL}${endpoint}`;
  const token = getStoredToken();
  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  let response = await fetch(url, { headers });
  if (!response.ok && (response.status === 404 || response.status === 502)) {
    // Try direct fallback
    const directUrl = `http://127.0.0.1:8000/api${endpoint}`;
    response = await fetch(directUrl, { headers });
  }

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    throw new Error(errorBody.detail || `Export failed with status ${response.status}`);
  }

  const blob = await response.blob();
  const disposition = response.headers.get('content-disposition');
  let filename = filenameFallback;
  if (disposition && disposition.includes('filename=')) {
    const match = disposition.match(/filename="?([^"]+)"?/);
    if (match && match[1]) filename = match[1];
  }

  const blobUrl = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = blobUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(blobUrl);
}

export const api = {
  // Health
  getHealth: () => fetchJson('/health'),

  // -------------------------------------------------------------
  // Authentication & Profile Management
  // -------------------------------------------------------------
  register: (userData) =>
    fetchJson('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    }),
  login: (username, password) =>
    fetchJson('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  getCurrentUser: () => fetchJson('/auth/me'),
  updateProfile: (profileData) =>
    fetchJson('/auth/profile', {
      method: 'PUT',
      body: JSON.stringify(profileData),
    }),
  changePassword: (currentPassword, newPassword) =>
    fetchJson('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    }),
  getPlatformUsers: () => fetchJson('/auth/users'),
  updateUserRole: (userId, role) =>
    fetchJson(`/auth/users/${userId}/role`, {
      method: 'PUT',
      body: JSON.stringify({ role }),
    }),

  // -------------------------------------------------------------
  // Locations
  // -------------------------------------------------------------
  getLocations: (status) => {
    const query = status ? `?status=${encodeURIComponent(status)}` : '';
    return fetchJson(`/locations${query}`);
  },
  createLocation: (locationData) =>
    fetchJson('/locations', {
      method: 'POST',
      body: JSON.stringify(locationData),
    }),

  // -------------------------------------------------------------
  // Telemetry Readings
  // -------------------------------------------------------------
  getReadings: ({ locationId, sourceType, startDate, endDate, page = 1, limit = 20 } = {}) => {
    const params = new URLSearchParams();
    if (locationId) params.append('location_id', locationId);
    if (sourceType) params.append('source_type', sourceType);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    params.append('page', page);
    params.append('limit', limit);
    return fetchJson(`/readings?${params.toString()}`);
  },
  createReading: (readingData) =>
    fetchJson('/readings', {
      method: 'POST',
      body: JSON.stringify(readingData),
    }),
  getHistoricalReadings: ({ locationId, sourceType, startDate, endDate, limit = 100 } = {}) => {
    const params = new URLSearchParams();
    if (locationId) params.append('location_id', locationId);
    if (sourceType) params.append('source_type', sourceType);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    params.append('limit', limit);
    return fetchJson(`/readings/history?${params.toString()}`);
  },

  // -------------------------------------------------------------
  // Environmental Data Ingestion & Sources
  // -------------------------------------------------------------
  ingestReading: (readingData) =>
    fetchJson('/ingestion/reading', {
      method: 'POST',
      body: JSON.stringify(readingData),
    }),
  ingestBatch: (readingsArray) =>
    fetchJson('/ingestion/batch', {
      method: 'POST',
      body: JSON.stringify(readingsArray),
    }),
  fetchRealData: (locationId = null) =>
    fetchJson('/ingestion/fetch-real', {
      method: 'POST',
      body: JSON.stringify(locationId ? { location_id: locationId } : {}),
    }),
  getIngestionStatus: () => fetchJson('/ingestion/status'),

  // -------------------------------------------------------------
  // Telemetry Simulator Controls
  // -------------------------------------------------------------
  getSimulatorStatus: () => fetchJson('/ingestion/simulate/status'),
  startSimulator: (intervalSeconds = null) => {
    const qs = intervalSeconds ? `?interval=${intervalSeconds}` : '';
    return fetchJson(`/ingestion/simulate/start${qs}`, { method: 'POST' });
  },
  stopSimulator: () => fetchJson('/ingestion/simulate/stop', { method: 'POST' }),
  seedHistoricalData: (days = 7) =>
    fetchJson(`/ingestion/historical/seed?days=${days}`, { method: 'POST' }),

  // -------------------------------------------------------------
  // Smart Alerts & Lifecycle Management
  // -------------------------------------------------------------
  getAlerts: ({ status, severity, locationId } = {}) => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (severity) params.append('severity', severity);
    if (locationId) params.append('location_id', locationId);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return fetchJson(`/alerts${qs}`);
  },
  getAlertStats: () => fetchJson('/alerts/stats'),
  createAlert: (alertData) =>
    fetchJson('/alerts', {
      method: 'POST',
      body: JSON.stringify(alertData),
    }),
  acknowledgeAlert: (alertId, notes = '') =>
    fetchJson(`/alerts/${alertId}/acknowledge`, {
      method: 'POST',
      body: JSON.stringify({ notes }),
    }),
  resolveAlert: (alertId, resolutionNotes = '') =>
    fetchJson(`/alerts/${alertId}/resolve`, {
      method: 'POST',
      body: JSON.stringify({ resolution_notes: resolutionNotes }),
    }),
  getAlertThresholds: () => fetchJson('/alerts/thresholds'),
  updateAlertThresholds: (thresholdConfig) =>
    fetchJson('/alerts/thresholds', {
      method: 'PUT',
      body: JSON.stringify(thresholdConfig),
    }),
  evaluateReadingThresholds: (readingData) =>
    fetchJson('/alerts/evaluate-reading', {
      method: 'POST',
      body: JSON.stringify(readingData),
    }),

  // -------------------------------------------------------------
  // Reporting & Audit Exports
  // -------------------------------------------------------------
  getSummaryReport: ({ locationId, sourceType, startDate, endDate } = {}) => {
    const params = new URLSearchParams();
    if (locationId) params.append('location_id', locationId);
    if (sourceType) params.append('source_type', sourceType);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return fetchJson(`/reports/summary${qs}`);
  },
  getReportTemplates: () => fetchJson('/reports/templates'),
  downloadReadingsCsv: ({ locationId = 'all', sourceType = 'all', startDate, endDate, limit = 5000 } = {}) => {
    const params = new URLSearchParams();
    if (locationId) params.append('location_id', locationId);
    if (sourceType) params.append('source_type', sourceType);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    params.append('limit', limit);
    return downloadFile(`/reports/readings/csv?${params.toString()}`, `ecopulse_telemetry_${locationId}.csv`);
  },
  downloadSummaryCsv: ({ locationId = 'all', sourceType = 'all', startDate, endDate } = {}) => {
    const params = new URLSearchParams();
    if (locationId) params.append('location_id', locationId);
    if (sourceType) params.append('source_type', sourceType);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    return downloadFile(`/reports/summary/csv?${params.toString()}`, `ecopulse_summary_${locationId}.csv`);
  },

  // -------------------------------------------------------------
  getAnalyticsSummary: (locationId = null) => {
    const qs = locationId && locationId !== 'all' ? `?location_id=${encodeURIComponent(locationId)}` : '';
    return fetchJson(`/analytics/summary${qs}`);
  },

  // -------------------------------------------------------------
  // Machine Learning & Predictive Forecasting
  // -------------------------------------------------------------
  getModelStatus: () => fetchJson('/forecast/model-status'),
  getForecast: ({ locationId = 'station-beta', horizonHours = 24 } = {}) =>
    fetchJson('/forecast/predict', {
      method: 'POST',
      body: JSON.stringify({
        location_id: locationId,
        horizon_hours: horizonHours,
      }),
    }),
  getForecastEvaluation: () => fetchJson('/forecast/evaluation'),
  retrainModel: ({ trainSource = 'sample_dataset', trainRatio = 0.8 } = {}) =>
    fetchJson('/forecast/train', {
      method: 'POST',
      body: JSON.stringify({
        train_source: trainSource,
        train_ratio: trainRatio,
      }),
    }),

  // Sample Seeding
  seedDatabase: () => fetchJson('/seed', { method: 'POST' }),
};

export default api;
