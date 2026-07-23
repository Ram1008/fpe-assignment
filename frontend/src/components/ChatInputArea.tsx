import React, { useState } from 'react';
import { useChatStore } from '../store/useChatStore';
import { Send, Sparkles } from 'lucide-react';

const SUGGESTED_PROMPTS = [
  "Target high value customers in US",
  "Target users with age >= 25 AND is_premium == true",
  "Add recently active users segment",
  "Remove segment high_value_customers"
];

export const ChatInputArea: React.FC = () => {
  const [text, setText] = useState('');
  const { sendMessage, isAgentThinking } = useChatStore();

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (text.trim() && !isAgentThinking) {
      sendMessage(text.trim());
      setText('');
    }
  };

  return (
    <div className="p-4 border-t border-slate-800 bg-slate-900/80">
      {/* Quick Prompts */}
      <div className="flex items-center gap-1.5 overflow-x-auto custom-scrollbar pb-2 mb-2">
        <span className="text-[11px] font-mono text-slate-500 flex items-center gap-1 shrink-0">
          <Sparkles className="w-3 h-3 text-indigo-400" /> Prompts:
        </span>
        {SUGGESTED_PROMPTS.map((prompt) => (
          <button
            key={prompt}
            onClick={() => setText(prompt)}
            className="px-2 py-1 bg-slate-800 hover:bg-slate-700 border border-slate-700/80 rounded-md text-[11px] text-slate-300 whitespace-nowrap transition"
          >
            {prompt}
          </button>
        ))}
      </div>

      <form onSubmit={handleSend} className="flex gap-2">
        <textarea
          rows={2}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSend(e);
            }
          }}
          placeholder="Describe your targeting rule in natural language... (Press Enter to send)"
          className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 transition custom-scrollbar resize-none"
        />
        <button
          type="submit"
          disabled={!text.trim() || isAgentThinking}
          className="px-4 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl font-semibold text-xs flex items-center justify-center gap-1.5 transition shadow-sm"
        >
          <Send className="w-4 h-4" /> Send
        </button>
      </form>
    </div>
  );
};
