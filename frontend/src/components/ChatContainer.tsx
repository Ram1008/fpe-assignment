import React, { useState } from 'react';
import { MessageList } from './MessageList';
import { ChatInputArea } from './ChatInputArea';
import { useChatStore } from '../store/useChatStore';
import { MessageSquare, Copy, Check } from 'lucide-react';

export const ChatContainer: React.FC = () => {
  const { messages } = useChatStore();
  const [copied, setCopied] = useState(false);

  const handleCopyCompleteChat = async () => {
    if (messages.length === 0) return;

    const formattedChat = messages
      .filter((m) => m.sender === 'user' || m.sender === 'agent')
      .map((m) => {
        const role = m.sender === 'user' ? 'User' : 'Agent';
        const timestamp = m.created_at
          ? ` [${new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}]`
          : '';
        let text = `${role}${timestamp}:\n${m.content}`;
        if (m.action_json && Array.isArray(m.action_json) && m.action_json.length > 0) {
          const actions = m.action_json.map((a: any) => a.action).join(', ');
          text += `\n[Actions Taken: ${actions}]`;
        }
        return text;
      })
      .join('\n\n---\n\n');

    try {
      await navigator.clipboard.writeText(formattedChat);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy chat to clipboard:', err);
    }
  };

  return (
    <div className="w-[440px] flex flex-col bg-slate-900/90 h-full border-r border-slate-800">
      {/* Chat Top Header Bar */}
      <div className="h-12 border-b border-slate-800 px-4 flex items-center justify-between bg-slate-900/50 shrink-0">
        <div className="flex items-center gap-2 text-slate-200 font-semibold text-sm">
          <MessageSquare className="w-4 h-4 text-indigo-400" />
          <span>Agent Chat</span>
          {messages.length > 0 && (
            <span className="text-[11px] font-mono font-normal px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
              {messages.length} msg{messages.length > 1 ? 's' : ''}
            </span>
          )}
        </div>

        <button
          onClick={handleCopyCompleteChat}
          title="Copy complete chat history"
          disabled={messages.length === 0}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition ${
            copied
              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
              : 'bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 disabled:opacity-40 disabled:cursor-not-allowed'
          }`}
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span>Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5 text-indigo-400" />
              <span>Copy Chat</span>
            </>
          )}
        </button>
      </div>

      <MessageList />
      <ChatInputArea />
    </div>
  );
};

