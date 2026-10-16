import React from 'react';
import {
  IconLeaf,
  IconPulse,
  IconActivity,
  IconMapPin,
  IconBrain,
  IconBarChart,
  IconBell,
  IconFileText,
  IconSettings,
  IconChevronLeft,
  IconChevronRight,
  IconRadio,
} from '../common/Icons';

export const NAV_ITEMS = [
  { id: 'overview', label: 'Overview', icon: IconPulse, badge: null },
  { id: 'live-monitoring', label: 'Live Monitoring', icon: IconActivity, badge: 'Live' },
  { id: 'environmental-map', label: 'Environmental Map', icon: IconMapPin, badge: null },
  { id: 'ai-predictions', label: 'AI Predictions', icon: IconBrain, badge: 'AI' },
  { id: 'analytics', label: 'Analytics', icon: IconBarChart, badge: null },
  { id: 'smart-alerts', label: 'Smart Alerts', icon: IconBell, badge: '4' },
  { id: 'reports', label: 'Reports', icon: IconFileText, badge: null },
  { id: 'settings', label: 'Settings', icon: IconSettings, badge: null },
];

export const Sidebar = ({
  currentTab,
  onSelectTab,
  isCollapsed,
  onToggleCollapse,
  mobileOpen,
  onCloseMobile,
}) => {
  return (
    <>
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          onClick={onCloseMobile}
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed lg:static top-0 bottom-0 left-0 z-50 flex flex-col bg-forest-950/95 lg:bg-forest-950/70 border-r border-forest-800/60 backdrop-blur-xl transition-all duration-300 ease-in-out ${
          isCollapsed ? 'w-20' : 'w-64'
        } ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}
      >
        {/* Brand Header */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-forest-800/60">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-700 flex items-center justify-center text-white shadow-lg shadow-emerald-500/20 shrink-0">
              <IconLeaf className="w-6 h-6" />
            </div>
            {!isCollapsed && (
              <div className="flex flex-col min-w-0">
                <span className="font-bold text-base tracking-tight text-white flex items-center gap-1.5">
                  EcoPulse <span className="text-emerald-400 text-xs font-semibold px-1.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">AI</span>
                </span>
                <span className="text-[10px] text-slate-400 tracking-wider uppercase truncate">
                  Environmental Intelligence
                </span>
              </div>
            )}
          </div>

          {/* Desktop Collapse Toggle */}
          <button
            onClick={onToggleCollapse}
            className="hidden lg:flex p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-forest-800/60 transition-colors"
            title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
          >
            {isCollapsed ? <IconChevronRight className="w-4 h-4" /> : <IconChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  onSelectTab(item.id);
                  if (onCloseMobile) onCloseMobile();
                }}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 shadow-sm shadow-emerald-500/10'
                    : 'text-slate-300 hover:text-white hover:bg-forest-800/40 border border-transparent'
                } ${isCollapsed ? 'justify-center' : 'justify-between'}`}
                title={isCollapsed ? item.label : undefined}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <Icon className={`w-5 h-5 shrink-0 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
                  {!isCollapsed && <span className="truncate">{item.label}</span>}
                </div>

                {!isCollapsed && item.badge && (
                  <span
                    className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full ${
                      item.badge === 'Live'
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 animate-pulse'
                        : item.badge === 'AI'
                        ? 'bg-teal-500/20 text-teal-300 border border-teal-500/30'
                        : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* System Health / Footer Info */}
        <div className="p-3 border-t border-forest-800/60">
          {!isCollapsed ? (
            <div className="p-3 rounded-xl bg-forest-900/60 border border-forest-800 flex items-center gap-3">
              <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
              <div className="min-w-0 flex-1">
                <p className="text-xs font-semibold text-slate-200 truncate">Telemetry Network</p>
                <p className="text-[10px] text-emerald-400 truncate">48 Nodes Operational</p>
              </div>
            </div>
          ) : (
            <div className="flex justify-center" title="48 Nodes Operational">
              <div className="w-3 h-3 rounded-full bg-emerald-400 ring-4 ring-emerald-500/20" />
            </div>
          )}
        </div>
      </aside>
    </>
  );
};
