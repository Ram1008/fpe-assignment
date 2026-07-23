import React, { useEffect, useRef, useState } from 'react';
import { useChatStore } from '../store/useChatStore';
import { ClarificationModal } from './ClarificationModal';
import { Bot, User, Cpu, Sparkles, CheckCircle2, Copy, Check } from 'lucide-react';

export const MessageList: React.FC = () => {
  const { messages, isAgentThinking } = useChatStore();
  const bottomRef = useRef<HTMLDivElement>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isAgentThinking]);

  const handleCopySingleMessage = async (id: string, content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      console.error('Failed to copy message:', err);
    }
  };

  return (
    <div className="flex-1 p-4 overflow-y-auto custom-scrollbar space-y-4">
      {messages.map((msg) => {
        const isUser = msg.sender === 'user';
        const isSystem = msg.sender === 'system';

        if (isSystem) {
          return (
            <div key={msg.id} className="p-3 bg-red-950/40 border border-red-500/30 rounded-xl text-xs text-red-300 font-mono">
              {msg.content}
            </div>
          );
        }

        return (
          <div
            key={msg.id}
            className={`group relative flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
          >
            {!isUser && (
              <div className="w-8 h-8 rounded-xl bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400 shrink-0">
                <Bot className="w-4 h-4" />
              </div>
            )}

            <div
              className={`relative max-w-[85%] rounded-2xl p-3.5 text-sm shadow-sm ${
                isUser
                  ? 'bg-indigo-600 text-white rounded-tr-none'
                  : 'bg-slate-800/90 text-slate-200 border border-slate-700/70 rounded-tl-none'
              }`}
            >
              <div className="whitespace-pre-wrap leading-relaxed">{msg.content}</div>

              {/* Action Badges */}
              {msg.action_json && Array.isArray(msg.action_json) && msg.action_json.length > 0 && (
                <div className="mt-2 pt-2 border-t border-slate-700/60 flex flex-wrap gap-1.5">
                  {msg.action_json.map((act: any, idx: number) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900/80 border border-indigo-500/30 text-indigo-300"
                    >
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                      {act.action}
                    </span>
                  ))}
                </div>
              )}

              <div className={`flex items-center justify-between gap-2 text-[10px] mt-1.5 font-mono ${isUser ? 'text-indigo-200' : 'text-slate-500'}`}>
                <span>{new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                <button
                  onClick={() => handleCopySingleMessage(msg.id, msg.content)}
                  title="Copy text"
                  className="opacity-0 group-hover:opacity-100 p-0.5 hover:bg-slate-700/50 rounded transition text-slate-300"
                >
                  {copiedId === msg.id ? (
                    <Check className="w-3 h-3 text-emerald-400" />
                  ) : (
                    <Copy className="w-3 h-3 text-slate-400 hover:text-white" />
                  )}
                </button>
              </div>
            </div>

            {isUser && (
              <div className="w-8 h-8 rounded-xl bg-slate-700 border border-slate-600 flex items-center justify-center text-slate-300 shrink-0">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        );
      })}

      {/* Pending Clarification Prompt */}
      <ClarificationModal />

      {/* Agent Thinking Indicator */}
      {isAgentThinking && (
        <div className="flex gap-3 items-center text-xs text-indigo-400 font-mono animate-pulse">
          <div className="w-8 h-8 rounded-xl bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center shrink-0">
            <Cpu className="w-4 h-4 animate-spin text-indigo-400" />
          </div>
          <span className="flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5" /> Agent reasoning and evaluating metadata...
          </span>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
};
