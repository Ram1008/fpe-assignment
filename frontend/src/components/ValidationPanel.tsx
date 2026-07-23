import React, { useState } from 'react';
import { useValidationStore } from '../store/useValidationStore';
import { CheckCircle2, XCircle, AlertTriangle, ShieldCheck, Download, ChevronUp, ChevronDown, Activity, Lightbulb } from 'lucide-react';

export const ValidationPanel: React.FC = () => {
  const { isValidating, isSubmitting, validationReport, submitSuccessMessage, triggerValidation, submitFinalTree } = useValidationStore();
  const [showDiagnostics, setShowDiagnostics] = useState(false);

  const isValid = validationReport?.ok === true;
  const summary = validationReport?.summary;
  const metrics = summary?.ast_metrics;
  const diagnostics = validationReport?.diagnostics;
  const errors = diagnostics?.errors || validationReport?.errors || [];
  const warnings = diagnostics?.warnings || validationReport?.warnings || [];
  const recommendations = validationReport?.recommendations_and_insights || [];

  return (
    <div className="border-t border-slate-800 bg-slate-900/95 backdrop-blur">
      {/* Success Notification Banner */}
      {submitSuccessMessage && (
        <div className="bg-emerald-950/80 border-b border-emerald-500/40 px-4 py-2 text-xs text-emerald-200 flex items-center justify-between">
          <span className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            {submitSuccessMessage}
          </span>
          <button
            onClick={() => useValidationStore.getState().clearSubmitStatus()}
            className="text-emerald-400 underline font-mono text-[11px]"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Expandable Profound Diagnostics & Recommendations Drawer */}
      {showDiagnostics && (
        <div className="p-4 bg-slate-950 border-b border-slate-800 max-h-64 overflow-y-auto custom-scrollbar space-y-3 text-xs font-mono">
          {/* Summary & Metrics */}
          {metrics && (
            <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 flex flex-wrap gap-4 text-slate-300">
              <span className="flex items-center gap-1">
                <Activity className="w-3.5 h-3.5 text-indigo-400" /> Total Nodes: <strong>{metrics.total_nodes}</strong>
              </span>
              <span>Tree Depth: <strong>{metrics.tree_depth}</strong></span>
              <span>Segments: <strong>{metrics.node_counts?.segments}</strong></span>
              <span>Attributes: <strong>{metrics.node_counts?.attributes}</strong></span>
              {summary?.validated_at && (
                <span className="text-slate-500 ml-auto">Validated: {new Date(summary.validated_at).toLocaleTimeString()}</span>
              )}
            </div>
          )}

          {/* Errors with Actionable Recommendations */}
          {errors.map((err: any, i: number) => (
            <div key={i} className="p-3 rounded-lg bg-red-950/40 border border-red-500/30 text-red-300 space-y-1">
              <div className="flex items-center gap-2 font-bold text-red-200">
                <XCircle className="w-4 h-4 text-red-400 shrink-0" />
                <span>Error at path: {err.path || '#'} ({err.code || 'VALIDATION_ERROR'})</span>
              </div>
              <div className="pl-6 text-slate-300">{err.message}</div>
              {err.actionable_recommendation && (
                <div className="ml-6 mt-1.5 p-2 rounded bg-amber-950/30 border border-amber-500/30 text-amber-200 flex items-start gap-1.5 text-[11px]">
                  <Lightbulb className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                  <div>
                    <strong>Actionable Fix:</strong> {err.actionable_recommendation}
                  </div>
                </div>
              )}
            </div>
          ))}

          {/* Warnings */}
          {warnings.map((warn: any, i: number) => (
            <div key={i} className="flex items-start gap-2 p-2.5 rounded-lg bg-amber-950/40 border border-amber-500/30 text-amber-300">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div>{typeof warn === 'string' ? warn : warn.message}</div>
            </div>
          ))}

          {/* Recommendations & Insights */}
          {recommendations.map((rec: any, i: number) => (
            <div key={i} className="flex items-start gap-2 p-2.5 rounded-lg bg-indigo-950/40 border border-indigo-500/30 text-indigo-300">
              <Lightbulb className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
              <div>
                <strong>{rec.title}:</strong> {rec.details}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Main Validation Footer Bar */}
      <div className="h-14 px-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {isValidating ? (
            <span className="flex items-center gap-2 text-xs text-indigo-400 font-mono">
              <ShieldCheck className="w-4 h-4 animate-spin text-indigo-400" /> Validating structure with Validator API...
            </span>
          ) : isValid ? (
            <button
              onClick={() => setShowDiagnostics(!showDiagnostics)}
              className="flex items-center gap-2 px-3 py-1 bg-emerald-950/60 border border-emerald-500/40 rounded-full text-xs font-semibold text-emerald-400 hover:bg-emerald-900/40 transition"
            >
              <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Tree Validated & Server Approved
              {metrics && <span className="text-[10px] font-mono text-emerald-300/80">({metrics.total_nodes} nodes, depth {metrics.tree_depth})</span>}
              {showDiagnostics ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronUp className="w-3.5 h-3.5" />}
            </button>
          ) : validationReport ? (
            <button
              onClick={() => setShowDiagnostics(!showDiagnostics)}
              className="flex items-center gap-2 px-3 py-1 bg-red-950/60 border border-red-500/40 rounded-full text-xs font-semibold text-red-400 hover:bg-red-900/40 transition"
            >
              <XCircle className="w-4 h-4 text-red-400" /> Invalid Tree ({errors.length} Error{errors.length === 1 ? '' : 's'})
              {showDiagnostics ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronUp className="w-3.5 h-3.5" />}
            </button>
          ) : (
            <span className="text-xs text-slate-400 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-slate-500" /> Validation Pending
            </span>
          )}
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={triggerValidation}
            disabled={isValidating}
            className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-xs font-semibold transition"
          >
            Re-Validate Tree
          </button>

          <button
            onClick={submitFinalTree}
            disabled={!isValid || isSubmitting}
            className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-xs font-bold transition shadow-sm ${
              isValid && !isSubmitting
                ? 'bg-emerald-600 hover:bg-emerald-500 text-white cursor-pointer'
                : 'bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed'
            }`}
          >
            <Download className="w-4 h-4" />
            {isSubmitting ? 'Exporting...' : 'Validate & Submit'}
          </button>
        </div>
      </div>
    </div>
  );
};

