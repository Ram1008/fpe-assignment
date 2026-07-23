import React from 'react';
import { useTreeStore } from '../store/useTreeStore';
import { TreeNodeComponent } from './TreeNodeComponent';
import { Network, Code2 } from 'lucide-react';

export const RecursiveTreeCanvas: React.FC = () => {
  const { tree } = useTreeStore();
  const [viewJson, setViewJson] = React.useState(false);

  return (
    <div className="flex-1 flex flex-col bg-slate-900/60 overflow-hidden relative border-l border-slate-800">
      {/* Visualizer Toolbar */}
      <div className="h-10 px-4 border-b border-slate-800 bg-slate-900/90 flex items-center justify-between z-10">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
          <Network className="w-4 h-4 text-indigo-400" />
          <span>Live Decision Tree Preview</span>
        </div>

        <button
          onClick={() => setViewJson(!viewJson)}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono transition ${
            viewJson
              ? 'bg-indigo-600 text-white'
              : 'bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-700'
          }`}
        >
          <Code2 className="w-3.5 h-3.5" />
          {viewJson ? 'Visual Tree' : 'View AST JSON'}
        </button>
      </div>

      {/* Canvas Area */}
      <div className="flex-1 p-6 overflow-y-auto custom-scrollbar">
        {!tree ? (
          <div className="h-full flex flex-col items-center justify-center text-center text-slate-500">
            <Network className="w-12 h-12 stroke-[1.2] mb-3 text-slate-600 animate-pulse" />
            <p className="font-semibold text-slate-400 text-sm">No Active Decision Tree</p>
            <p className="text-xs text-slate-500 max-w-xs mt-1">
              Start chatting with the AI agent on the left to build targeting rules.
            </p>
          </div>
        ) : viewJson ? (
          <pre className="p-4 bg-slate-950 rounded-xl border border-slate-800 text-xs font-mono text-emerald-400 overflow-x-auto">
            {JSON.stringify(tree, null, 2)}
          </pre>
        ) : (
          <div className="max-w-2xl mx-auto">
            <TreeNodeComponent node={tree} />
          </div>
        )}
      </div>
    </div>
  );
};
