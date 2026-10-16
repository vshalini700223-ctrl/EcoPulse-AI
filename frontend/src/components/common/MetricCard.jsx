import React from 'react';
import { StatusBadge } from './StatusBadge';

export const MetricCard = ({
  title,
  value,
  unit,
  icon: Icon,
  delta,
  deltaText,
  isPositiveGood = true,
  statusLabel,
  statusVariant,
  subtitle,
  className = "",
}) => {
  const isGood = delta && ((delta > 0 && isPositiveGood) || (delta < 0 && !isPositiveGood));

  return (
    <div className={`eco-card eco-card-interactive p-5 relative overflow-hidden group ${className}`}>
      {/* Subtle background ambient corner glow */}
      <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-bl-full pointer-events-none group-hover:bg-emerald-500/10 transition-colors" />

      <div className="flex items-start justify-between relative z-10">
        <div>
          <p className="text-xs font-medium text-emerald-300/70 tracking-wider uppercase">{title}</p>
          <div className="flex items-baseline gap-1.5 mt-2">
            <span className="text-2xl sm:text-3xl font-bold tracking-tight text-white">{value}</span>
            {unit && <span className="text-sm font-medium text-slate-400">{unit}</span>}
          </div>
        </div>

        {Icon && (
          <div className="p-2.5 rounded-xl bg-forest-800/80 border border-emerald-500/20 text-emerald-400 group-hover:text-emerald-300 group-hover:border-emerald-500/40 transition-colors">
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      <div className="mt-4 pt-3 border-t border-forest-700/40 flex items-center justify-between text-xs">
        {statusLabel && (
          <StatusBadge variant={statusVariant || 'good'} label={statusLabel} size="xs" />
        )}

        {delta !== undefined && (
          <div className={`flex items-center gap-1 font-medium ${isGood ? 'text-emerald-400' : 'text-amber-400'}`}>
            <span>{delta > 0 ? `+${delta}%` : `${delta}%`}</span>
            <span className="text-slate-400 text-[11px]">{deltaText || 'vs last hr'}</span>
          </div>
        )}

        {subtitle && !delta && (
          <span className="text-slate-400 text-xs truncate">{subtitle}</span>
        )}
      </div>
    </div>
  );
};
