import React from 'react';
import { TreeNode } from '../types';
import { Tag, Sliders, Layers } from 'lucide-react';

interface Props {
  node: TreeNode;
  depth?: number;
}

export const TreeNodeComponent: React.FC<Props> = ({ node, depth = 0 }) => {
  if (!node) return null;

  if (node.type === 'AND' || node.type === 'OR') {
    const isAnd = node.type === 'AND';
    return (
      <div
        className={`my-2 p-3.5 rounded-xl border transition-all ${
          isAnd
            ? 'border-sky-500/40 bg-sky-950/20 shadow-sky-950/50 shadow-sm'
            : 'border-amber-500/40 bg-amber-950/20 shadow-amber-950/50 shadow-sm'
        }`}
      >
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span
              className={`px-2 py-0.5 rounded text-xs font-bold font-mono uppercase tracking-wider text-white shadow-sm ${
                isAnd ? 'bg-sky-600' : 'bg-amber-600'
              }`}
            >
              {node.type}
            </span>
            <span className="text-xs text-slate-400 font-mono">
              ({node.children?.length || 0} condition{node.children?.length === 1 ? '' : 's'})
            </span>
          </div>
          <span className="text-[10px] font-mono text-slate-500 hover:text-slate-400">
            {node.id}
          </span>
        </div>

        <div className="pl-3.5 border-l-2 border-slate-700/60 space-y-2">
          {node.children && node.children.length > 0 ? (
            node.children.map((child) => (
              <TreeNodeComponent key={child.id} node={child} depth={depth + 1} />
            ))
          ) : (
            <div className="text-xs text-slate-500 italic py-1">
              Empty boolean group. Ask agent to add conditions.
            </div>
          )}
        </div>
      </div>
    );
  }

  if (node.type === 'segment') {
    return (
      <div className="flex items-center justify-between p-2.5 bg-emerald-950/30 border border-emerald-500/40 rounded-lg text-emerald-300 my-1.5 shadow-sm hover:border-emerald-500/70 transition">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 bg-emerald-900/50 rounded text-emerald-400">
            <Tag className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs text-emerald-400/80 font-mono">Segment</div>
            <div className="font-mono text-sm font-semibold text-emerald-200">{node.key}</div>
          </div>
        </div>
        <span className="text-[10px] font-mono text-slate-500">{node.id}</span>
      </div>
    );
  }

  // Attribute Predicate Node
  if (node.type === 'attribute') {
    return (
      <div className="flex items-center justify-between p-2.5 bg-purple-950/30 border border-purple-500/40 rounded-lg text-purple-300 my-1.5 shadow-sm hover:border-purple-500/70 transition">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 bg-purple-900/50 rounded text-purple-400">
            <Sliders className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs text-purple-400/80 font-mono">Attribute Filter</div>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="font-mono text-sm font-semibold text-purple-200">{node.attribute}</span>
              <span className="font-mono text-xs font-bold bg-purple-900 px-1.5 py-0.5 rounded border border-purple-700 text-purple-200">
                {node.operator}
              </span>
              <span className="font-mono text-sm text-slate-100 font-semibold">
                {JSON.stringify(node.value)}
              </span>
            </div>
          </div>
        </div>
        <span className="text-[10px] font-mono text-slate-500">{node.id}</span>
      </div>
    );
  }

  return null;
};
