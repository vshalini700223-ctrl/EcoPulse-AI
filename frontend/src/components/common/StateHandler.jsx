import React from 'react';
import { IconAlertTriangle, IconRefresh, IconLeaf, IconActivity } from './Icons';

export const LoadingSkeleton = ({ count = 3, type = "card" }) => {
  if (type === "card") {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="eco-card p-5 h-36 flex flex-col justify-between">
            <div className="flex justify-between items-center">
              <div className="h-3 w-24 bg-forest-700/60 rounded" />
              <div className="h-8 w-8 bg-forest-700/60 rounded-xl" />
            </div>
            <div className="h-8 w-28 bg-forest-700/80 rounded my-2" />
            <div className="h-3 w-36 bg-forest-700/40 rounded" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="eco-card p-6 h-72 flex flex-col items-center justify-center gap-4 animate-pulse">
      <div className="w-12 h-12 rounded-full bg-forest-700/60 flex items-center justify-center text-emerald-400/50">
        <IconActivity className="w-6 h-6 animate-spin" />
      </div>
      <div className="h-4 w-48 bg-forest-700/60 rounded" />
      <div className="h-3 w-64 bg-forest-700/40 rounded" />
    </div>
  );
};

export const EmptyState = ({
  title = "No Environmental Telemetry Found",
  message = "No sensor readings match the selected station or date range filter.",
  onReset,
}) => {
  return (
    <div className="eco-card p-10 text-center flex flex-col items-center justify-center my-6">
      <div className="w-14 h-14 rounded-2xl bg-forest-800 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mb-4">
        <IconLeaf className="w-7 h-7" />
      </div>
      <h3 className="text-lg font-semibold text-white mb-1">{title}</h3>
      <p className="text-sm text-slate-400 max-w-md mb-6">{message}</p>
      {onReset && (
        <button
          onClick={onReset}
          className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/30 transition-colors"
        >
          <IconRefresh className="w-3.5 h-3.5" />
          Reset Filters
        </button>
      )}
    </div>
  );
};

export const ErrorState = ({
  title = "Sensor Network Connection Error",
  message = "Failed to synchronize with atmospheric telemetry feeds. Backend stream may be offline or unreachable.",
  onRetry,
}) => {
  return (
    <div className="eco-card border-rose-500/30 bg-gradient-to-r from-rose-950/40 via-forest-900/60 to-forest-900/60 p-6 my-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="p-2.5 rounded-xl bg-rose-500/20 border border-rose-500/40 text-rose-400 shrink-0">
            <IconAlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-rose-200">{title}</h4>
            <p className="text-xs text-rose-300/80 mt-1 max-w-xl">{message}</p>
          </div>
        </div>
        {onRetry && (
          <button
            onClick={onRetry}
            className="inline-flex items-center gap-2 px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-rose-500/20 text-rose-200 border border-rose-500/40 hover:bg-rose-500/30 transition-colors shrink-0"
          >
            <IconRefresh className="w-3.5 h-3.5" />
            Retry Stream
          </button>
        )}
      </div>
    </div>
  );
};
