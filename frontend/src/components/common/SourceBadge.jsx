import React from 'react';
import { IconCloud, IconCpu, IconHistory } from './Icons';

/**
 * Visual badge indicating whether environmental data is from
 * a verified real API, simulated telemetry stream, or historical dataset.
 */
export const SourceBadge = ({ sourceType = 'simulated', provider = null, size = 'sm' }) => {
  const normalized = sourceType?.toLowerCase() || '';
  const isReal = normalized === 'real' || normalized === 'real_api' || normalized.includes('real');
  const isHistorical = normalized === 'historical' || normalized === 'historical_sample' || normalized.includes('history');

  const badgeStyle = isReal
    ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 shadow-[0_0_12px_rgba(16,185,129,0.15)]'
    : isHistorical
    ? 'bg-sky-500/20 text-sky-300 border-sky-500/40 shadow-[0_0_12px_rgba(14,165,233,0.15)]'
    : 'bg-purple-500/20 text-purple-300 border-purple-500/40 shadow-[0_0_12px_rgba(168,85,247,0.15)]';

  const dotStyle = isReal
    ? 'bg-emerald-400'
    : isHistorical
    ? 'bg-sky-400'
    : 'bg-purple-400';

  const Icon = isReal ? IconCloud : isHistorical ? IconHistory : IconCpu;
  const labelText = isReal
    ? `Real API ${provider ? `· ${provider}` : ''}`
    : isHistorical
    ? `Historical ${provider ? `· ${provider}` : 'Dataset'}`
    : 'Simulated';

  const sizeClasses = size === 'xs'
    ? 'text-[10px] px-2 py-0.5'
    : 'text-xs font-semibold px-2.5 py-1';

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border backdrop-blur-md font-mono ${badgeStyle} ${sizeClasses}`}
      title={isReal ? 'Verified live external weather & atmospheric API feed' : isHistorical ? 'Historical observational dataset' : 'Synthesized continuous sensor telemetry'}
    >
      <span className="relative flex h-2 w-2">
        <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${dotStyle}`} />
        <span className={`relative inline-flex rounded-full h-2 w-2 ${dotStyle}`} />
      </span>
      <Icon className="w-3.5 h-3.5" />
      <span>{labelText}</span>
    </span>
  );
};

export default SourceBadge;
