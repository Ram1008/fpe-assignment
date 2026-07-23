import React, { useEffect } from 'react';
import { useCacheStore } from '../store/useCacheStore';
import { useChatStore } from '../store/useChatStore';
import { Network, Database, RefreshCw, PlusCircle, History } from 'lucide-react';

export const HeaderBar: React.FC = () => {
  const { cacheStatus, fetchStatus, triggerRefresh } = useCacheStore();
  const { conversationId, conversationsList, initConversation, loadConversation, fetchConversationsList } = useChatStore();

  useEffect(() => {
    fetchStatus();
    fetchConversationsList();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-14 border-b border-slate-800 bg-slate-900/90 backdrop-blur px-6 flex items-center justify-between z-20">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-indigo-600/20 border border-indigo-500/30 rounded-lg text-indigo-400">
          <Network className="w-5 h-5" />
        </div>
        <div>
          <h1 className="font-bold text-base text-slate-100 flex items-center gap-2">
            AI Decision-Tree Agent
            <span className="text-xs font-mono font-normal px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
              localhost:3000
            </span>
          </h1>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Cache status badge */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700 text-xs font-mono">
          <Database className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-slate-400">Cache:</span>
          {cacheStatus?.is_bootstrapping ? (
            <span className="text-amber-400 flex items-center gap-1 animate-pulse">
              <RefreshCw className="w-3 h-3 animate-spin" /> BOOTSTRAPPING
            </span>
          ) : cacheStatus?.status === 'READY' ? (
            <span className="text-emerald-400 font-semibold">
              READY ({cacheStatus.segments_count} segs, 24h TTL)
            </span>
          ) : (
            <span className="text-slate-300 font-semibold">{cacheStatus?.status || 'INITIALIZING'}</span>
          )}
          <button
            onClick={triggerRefresh}
            title="Refresh cache"
            className="p-1 hover:bg-slate-700 rounded text-slate-400 hover:text-white transition"
          >
            <RefreshCw className="w-3 h-3" />
          </button>
        </div>

        {/* Sessions Dropdown */}
        <div className="flex items-center gap-2">
          {conversationsList.length > 0 && (
            <select
              value={conversationId || ''}
              onChange={(e) => loadConversation(e.target.value)}
              className="bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-indigo-500"
            >
              {conversationsList.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.title} ({c.id.slice(-4)})
                </option>
              ))}
            </select>
          )}

          <button
            onClick={initConversation}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium transition shadow-sm"
          >
            <PlusCircle className="w-3.5 h-3.5" /> New Tree
          </button>
        </div>
      </div>
    </header>
  );
};
