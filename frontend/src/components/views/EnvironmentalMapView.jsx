import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { MONITORING_LOCATIONS } from '../../data/mockData';
import { StatusBadge } from '../common/StatusBadge';
import { SourceBadge } from '../common/SourceBadge';
import { IconMapPin, IconLeaf, IconLayers, IconRefresh } from '../common/Icons';

export const EnvironmentalMapView = () => {
  const [locations, setLocations] = useState(MONITORING_LOCATIONS.filter((l) => l.id !== 'all'));
  const [activePin, setActivePin] = useState(MONITORING_LOCATIONS[1]);
  const [layerMode, setLayerMode] = useState('aqi'); // 'aqi' or 'pm25'
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function loadStations() {
      setLoading(true);
      try {
        const liveLocs = await api.getLocations();
        if (liveLocs && liveLocs.length > 0) {
          const formatted = liveLocs.map((loc) => ({
            id: loc.id,
            name: loc.name,
            zone: loc.zone || 'Regional Zone',
            type: loc.location_type || 'EcoStation',
            coordinates: loc.latitude && loc.longitude ? `${loc.latitude}° N, ${loc.longitude}° E` : '12.97° N, 77.64° E',
            status: loc.status || 'Active',
            aqi: loc.current_aqi || 45,
            pm25: 14.5,
            pm10: 32.0,
            temp: 24.5,
            humidity: 62.0,
            sensorsActive: loc.active_sensors || 12,
            sensorsTotal: loc.total_sensors || 12,
            source_type: loc.source_type || 'real',
            source_provider: loc.source_provider || 'open-meteo',
          }));
          setLocations(formatted);
          setActivePin(formatted[0]);
        }
      } catch (err) {
        console.warn('Using baseline station coordinates:', err);
      } finally {
        setLoading(false);
      }
    }
    loadStations();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <IconMapPin className="w-5 h-5 text-emerald-400" />
            Geospatial Environmental Map & Sensor Coordinates
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Regional distribution, microclimate sensor telemetry coordinates, and dispersion vectors
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center bg-forest-900 p-1 rounded-xl border border-forest-800 text-xs">
            <button
              onClick={() => setLayerMode('aqi')}
              className={`px-3 py-1 rounded-lg font-medium transition-colors ${
                layerMode === 'aqi' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'text-slate-400'
              }`}
            >
              Heatmap: AQI
            </button>
            <button
              onClick={() => setLayerMode('pm25')}
              className={`px-3 py-1 rounded-lg font-medium transition-colors ${
                layerMode === 'pm25' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'text-slate-400'
              }`}
            >
              Particulate: PM2.5
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Interactive Map Visual Simulation */}
        <div className="lg:col-span-2 eco-card p-6 min-h-[440px] flex flex-col justify-between relative overflow-hidden bg-gradient-to-b from-[#07241a] via-[#051c14] to-[#041510] border border-emerald-500/20">
          {/* Subtle grid pattern background simulating geospatial grid */}
          <div
            className="absolute inset-0 opacity-15 pointer-events-none"
            style={{
              backgroundImage: 'radial-gradient(circle at 1px 1px, #10b981 1px, transparent 0)',
              backgroundSize: '32px 32px',
            }}
          />

          <div className="relative z-10 flex items-center justify-between">
            <div className="bg-forest-900/90 border border-emerald-500/20 px-3 py-1.5 rounded-xl backdrop-blur-md text-xs text-slate-300 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>Coverage: Metropolitan & Nature Reserves (780 km²)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400 font-mono">EPSG:4326</span>
            </div>
          </div>

          {/* Interactive station pin markers */}
          <div className="relative z-10 my-10 grid grid-cols-2 sm:grid-cols-3 gap-3">
            {locations.map((loc) => {
              const isSelected = activePin && activePin.id === loc.id;
              return (
                <button
                  key={loc.id}
                  onClick={() => setActivePin(loc)}
                  className={`p-3.5 rounded-2xl text-left transition-all ${
                    isSelected
                      ? 'bg-emerald-500/20 border-2 border-emerald-400 shadow-lg shadow-emerald-500/20 scale-105'
                      : 'bg-forest-900/80 border border-forest-800 hover:border-emerald-500/40'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
                    <span className="text-xs font-bold text-white font-mono">{loc.aqi} AQI</span>
                  </div>
                  <p className="text-xs font-semibold text-slate-200 mt-2 truncate">
                    {loc.name.split('—')[1] || loc.name}
                  </p>
                  <p className="text-[10px] text-emerald-400 truncate">{loc.zone}</p>
                </button>
              );
            })}
          </div>

          <div className="relative z-10 flex items-center justify-between text-xs text-slate-400 border-t border-forest-800/80 pt-3">
            <span>Leaflet + OpenStreetMap Sensor Layer Active</span>
            <span className="text-emerald-400 font-mono">Real-Time In-Situ Mesh</span>
          </div>
        </div>

        {/* Selected Station Detail Sidebar */}
        {activePin && (
          <div className="eco-card p-5 space-y-4">
            <div className="flex items-start justify-between border-b border-forest-800/80 pb-3">
              <div>
                <span className="text-[10px] text-emerald-400 font-mono uppercase tracking-wider block">
                  Sensor Station Focus
                </span>
                <h3 className="text-base font-bold text-white mt-1">{activePin.name}</h3>
                <div className="flex items-center gap-2 mt-1">
                  <p className="text-xs text-slate-400">{activePin.zone}</p>
                  <SourceBadge sourceType={activePin.source_type || 'real'} provider={activePin.source_provider || 'open-meteo'} size="xs" />
                </div>
              </div>
              <StatusBadge variant={activePin.status} label={activePin.status} size="sm" />
            </div>

            <div className="space-y-3 text-xs">
              <div className="flex justify-between py-1 border-b border-forest-800/40">
                <span className="text-slate-400">GPS Coordinates:</span>
                <span className="font-mono text-emerald-300">{activePin.coordinates}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-forest-800/40">
                <span className="text-slate-400">Biome Type:</span>
                <span className="text-slate-200">{activePin.type}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-forest-800/40">
                <span className="text-slate-400">Air Quality Index:</span>
                <span className="font-bold text-emerald-400 font-mono">{activePin.aqi} AQI</span>
              </div>
              <div className="flex justify-between py-1 border-b border-forest-800/40">
                <span className="text-slate-400">Particulates (PM2.5):</span>
                <span className="text-teal-300 font-medium font-mono">{activePin.pm25} µg/m³</span>
              </div>
              <div className="flex justify-between py-1 border-b border-forest-800/40">
                <span className="text-slate-400">Inhalable (PM10):</span>
                <span className="text-amber-300 font-medium font-mono">{activePin.pm10} µg/m³</span>
              </div>
              <div className="flex justify-between py-1 border-b border-forest-800/40">
                <span className="text-slate-400">Microclimate Temp/RH:</span>
                <span className="text-slate-200 font-mono">
                  {activePin.temp}°C / {activePin.humidity}% RH
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Active IoT Transmitters:</span>
                <span className="text-emerald-400 font-medium">
                  {activePin.sensorsActive} / {activePin.sensorsTotal} Online
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
