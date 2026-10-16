import React, { useState } from 'react';
import {
  IconMenu,
  IconMapPin,
  IconRefresh,
  IconBell,
  IconUser,
  IconShield,
  IconSettings,
} from '../common/Icons';
import { MONITORING_LOCATIONS } from '../../data/mockData';
import { useAuth } from '../../context/AuthContext';

export const TopNav = ({
  onToggleMobile,
  selectedStationId,
  onSelectStation,
  timeRange,
  onSelectTimeRange,
  onRefresh,
  isRefreshing,
  viewState,
  onToggleViewState,
  onOpenAuth,
  activeAlertCount = 3,
  onNavigateTab,
}) => {
  const { user, isAuthenticated, logout } = useAuth();
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);

  return (
    <header className="h-16 bg-forest-950/70 border-b border-forest-800/60 backdrop-blur-xl sticky top-0 z-30 px-4 sm:px-6 flex items-center justify-between gap-4">
      {/* Mobile Menu & Current Context */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleMobile}
          className="lg:hidden p-2 rounded-lg text-slate-300 hover:text-white hover:bg-forest-800/60 transition-colors"
          aria-label="Open Navigation Menu"
        >
          <IconMenu className="w-5 h-5" />
        </button>

        <div className="hidden sm:flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs font-medium text-emerald-400">Live Telemetry Stream</span>
        </div>
      </div>

      {/* Selectors and Controls */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Location Selector */}
        <div className="relative flex items-center">
          <IconMapPin className="w-4 h-4 text-emerald-400 absolute left-3 pointer-events-none" />
          <select
            value={selectedStationId}
            onChange={(e) => onSelectStation(e.target.value)}
            className="pl-8 pr-8 py-1.5 bg-forest-900/80 border border-emerald-500/20 text-slate-200 text-xs rounded-xl focus:outline-none focus:border-emerald-500/50 hover:border-emerald-500/40 transition-colors appearance-none cursor-pointer max-w-[140px] sm:max-w-[200px] truncate"
          >
            <option value="all" className="bg-forest-900 text-white">All Monitored Stations</option>
            {MONITORING_LOCATIONS.map((loc) => (
              <option key={loc.id} value={loc.id} className="bg-forest-900 text-white">
                {loc.name}
              </option>
            ))}
          </select>
        </div>

        {/* Date / Time Range Selector */}
        <div className="hidden md:block">
          <select
            value={timeRange}
            onChange={(e) => onSelectTimeRange(e.target.value)}
            className="px-3 py-1.5 bg-forest-900/80 border border-emerald-500/20 text-slate-200 text-xs rounded-xl focus:outline-none focus:border-emerald-500/50 hover:border-emerald-500/40 transition-colors appearance-none cursor-pointer"
          >
            <option value="24h" className="bg-forest-900 text-white">Last 24 Hours</option>
            <option value="today" className="bg-forest-900 text-white">Today</option>
            <option value="7d" className="bg-forest-900 text-white">Last 7 Days</option>
            <option value="30d" className="bg-forest-900 text-white">Last 30 Days</option>
          </select>
        </div>

        {/* State Simulator Selector (Loading / Empty / Error demonstration) */}
        <div className="hidden xl:flex items-center gap-1 bg-forest-900/60 p-1 rounded-xl border border-forest-800 text-[11px]">
          <span className="text-slate-400 px-2 font-medium">State:</span>
          {['normal', 'loading', 'empty', 'error'].map((st) => (
            <button
              key={st}
              onClick={() => onToggleViewState(st)}
              className={`px-2 py-0.5 rounded-lg capitalize transition-colors ${
                viewState === st
                  ? 'bg-emerald-500/20 text-emerald-300 font-semibold border border-emerald-500/40'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        {/* Refresh Action */}
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="p-2 rounded-xl bg-forest-900/80 border border-emerald-500/20 text-slate-300 hover:text-white hover:border-emerald-500/40 transition-colors"
          title="Refresh Telemetry Data"
        >
          <IconRefresh className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-emerald-400' : ''}`} />
        </button>

        {/* Alerts Pill */}
        <div className="relative">
          <button
            onClick={() => onNavigateTab && onNavigateTab('smart-alerts')}
            className="p-2 rounded-xl bg-forest-900/80 border border-emerald-500/20 text-slate-300 hover:text-white hover:border-emerald-500/40 transition-colors relative"
            title={`${activeAlertCount} Active Environmental Alerts`}
          >
            <IconBell className="w-4 h-4" />
            {activeAlertCount > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-rose-500 text-white text-[10px] font-bold flex items-center justify-center ring-2 ring-forest-950 animate-pulse">
                {activeAlertCount}
              </span>
            )}
          </button>
        </div>

        {/* User Authentication Status & Profile Menu */}
        {isAuthenticated && user ? (
          <div className="relative">
            <button
              onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
              className="flex items-center gap-2 pl-2 pr-3 py-1.5 bg-forest-900/90 border border-emerald-500/30 rounded-xl hover:border-emerald-500/50 transition-colors"
            >
              <div className="w-7 h-7 rounded-lg bg-emerald-500/20 text-emerald-300 font-bold text-xs flex items-center justify-center border border-emerald-500/40">
                {user.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
              </div>
              <div className="hidden sm:block text-left">
                <span className="text-xs font-semibold text-white block leading-tight truncate max-w-[100px]">
                  {user.full_name || user.username}
                </span>
                <span className="text-[10px] text-emerald-400 font-mono capitalize">
                  {user.role === 'admin' ? 'Admin' : user.role === 'field_operator' ? 'Operator' : 'Analyst'}
                </span>
              </div>
            </button>

            {/* Profile Dropdown */}
            {profileDropdownOpen && (
              <div className="absolute right-0 mt-2 w-56 rounded-2xl bg-[#062016] border border-emerald-500/30 shadow-2xl p-2 z-50 animate-fade-in">
                <div className="p-3 border-b border-forest-800">
                  <p className="text-xs font-bold text-white">{user.full_name}</p>
                  <p className="text-[11px] text-slate-400 truncate">{user.email}</p>
                  <span className="inline-block mt-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    Role: {user.role}
                  </span>
                </div>
                <div className="py-1">
                  <button
                    onClick={() => {
                      setProfileDropdownOpen(false);
                      onNavigateTab && onNavigateTab('settings');
                    }}
                    className="w-full flex items-center gap-2 px-3 py-2 text-xs text-slate-300 hover:text-white hover:bg-forest-800/60 rounded-xl transition-colors"
                  >
                    <IconSettings className="w-4 h-4 text-emerald-400" />
                    <span>Settings & Profile</span>
                  </button>
                  <button
                    onClick={() => {
                      setProfileDropdownOpen(false);
                      logout();
                    }}
                    className="w-full flex items-center gap-2 px-3 py-2 text-xs text-rose-300 hover:text-rose-200 hover:bg-rose-500/10 rounded-xl transition-colors mt-1"
                  >
                    <IconUser className="w-4 h-4 text-rose-400" />
                    <span>Sign Out</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <button
            onClick={onOpenAuth}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 hover:bg-emerald-500/30 transition-all shadow-sm"
          >
            <IconShield className="w-4 h-4" />
            <span>Sign In</span>
          </button>
        )}
      </div>
    </header>
  );
};
