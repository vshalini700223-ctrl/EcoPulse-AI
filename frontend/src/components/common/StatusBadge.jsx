import React from 'react';

export const StatusBadge = ({ variant = 'default', label, size = 'sm' }) => {
  const getStyle = () => {
    switch (variant.toLowerCase()) {
      case 'good':
      case 'success':
      case 'healthy':
      case 'online':
        return 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30';
      case 'moderate':
      case 'warning':
      case 'sensitive':
        return 'bg-amber-500/15 text-amber-300 border-amber-500/30';
      case 'critical':
      case 'unhealthy':
      case 'error':
        return 'bg-rose-500/15 text-rose-300 border-rose-500/30';
      case 'info':
      case 'teal':
        return 'bg-teal-500/15 text-teal-300 border-teal-500/30';
      default:
        return 'bg-slate-700/30 text-slate-300 border-slate-600/30';
    }
  };

  const getDotStyle = () => {
    switch (variant.toLowerCase()) {
      case 'good':
      case 'success':
      case 'healthy':
      case 'online':
        return 'bg-emerald-400';
      case 'moderate':
      case 'warning':
      case 'sensitive':
        return 'bg-amber-400';
      case 'critical':
      case 'unhealthy':
      case 'error':
        return 'bg-rose-400';
      case 'info':
      case 'teal':
        return 'bg-teal-400';
      default:
        return 'bg-slate-400';
    }
  };

  const sizeClasses = size === 'xs' 
    ? 'text-xs px-2 py-0.5' 
    : 'text-xs font-medium px-2.5 py-1';

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border ${getStyle()} ${sizeClasses}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${getDotStyle()} animate-pulse`} />
      {label}
    </span>
  );
};
