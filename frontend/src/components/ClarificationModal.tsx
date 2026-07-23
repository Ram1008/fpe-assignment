import React, { useState } from 'react';
import { useChatStore } from '../store/useChatStore';
import { HelpCircle, Send } from 'lucide-react';

export const ClarificationModal: React.FC = () => {
  const { pendingClarification, submitClarification } = useChatStore();
  const [customText, setCustomText] = useState('');

  if (!pendingClarification) return null;

  const handleSubmitCustom = (e: React.FormEvent) => {
    e.preventDefault();
    if (customText.trim()) {
      submitClarification(customText.trim());
      setCustomText('');
    }
  };

  return (
    <div className="mx-4 my-2 p-4 bg-amber-950/40 border-2 border-amber-500/50 rounded-xl shadow-lg animate-in fade-in">
      <div className="flex items-start gap-3">
        <div className="p-2 bg-amber-600/20 border border-amber-500/30 rounded-lg text-amber-400">
          <HelpCircle className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <h4 className="text-xs font-bold font-mono text-amber-400 uppercase tracking-wider mb-1">
            Agent Clarification Request
          </h4>
          <p className="text-sm text-slate-100 font-medium mb-3">
            {pendingClarification.question}
          </p>

          {/* Option Pills */}
          {pendingClarification.options && pendingClarification.options.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-3">
              {pendingClarification.options.map((opt) => (
                <button
                  key={opt}
                  onClick={() => submitClarification(opt)}
                  className="px-3 py-1.5 bg-amber-900/60 hover:bg-amber-800 border border-amber-500/40 rounded-lg text-xs font-mono text-amber-200 transition"
                >
                  {opt}
                </button>
              ))}
            </div>
          )}

          {/* Custom Input */}
          <form onSubmit={handleSubmitCustom} className="flex gap-2">
            <input
              type="text"
              value={customText}
              onChange={(e) => setCustomText(e.target.value)}
              placeholder="Or type custom clarification..."
              className="flex-1 bg-slate-900 border border-slate-700 text-xs rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-amber-500"
            />
            <button
              type="submit"
              disabled={!customText.trim()}
              className="px-3 py-2 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center gap-1 transition"
            >
              <Send className="w-3.5 h-3.5" /> Answer
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
