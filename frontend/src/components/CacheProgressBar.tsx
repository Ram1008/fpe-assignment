import React from 'react';
import { useCacheStore } from '../store/useCacheStore';
import { RefreshCw } from 'lucide-react';

export const CacheProgressBar: React.FC = () => {
  const { cacheStatus } = useCacheStore();

  if (!cacheStatus?.is_bootstrapping) return null;

  return (
    <div className="bg-amber-950/60 border-b border-amber-500/30 px-4 py-2 text-xs text-amber-200 flex items-center justify-between animate-pulse">
      <div className="flex items-center gap-2">
        <RefreshCw className="w-3.5 h-3.5 animate-spin text-amber-400" />
        <span>
          <strong>Hybrid Async Bootstrapping:</strong> Discovering segment keys and attribute definitions from Users API...
        </span>
      </div>
      <div className="font-mono text-amber-400 font-semibold">
        {cacheStatus.segments_count} segments found so far
      </div>
    </div>
  );
};
