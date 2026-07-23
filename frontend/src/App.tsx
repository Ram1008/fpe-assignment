import React, { useEffect } from 'react';
import { HeaderBar } from './components/HeaderBar';
import { CacheProgressBar } from './components/CacheProgressBar';
import { ChatContainer } from './components/ChatContainer';
import { RecursiveTreeCanvas } from './components/RecursiveTreeCanvas';
import { ValidationPanel } from './components/ValidationPanel';
import { useChatStore } from './store/useChatStore';

export const App: React.FC = () => {
  const { initConversation, conversationId } = useChatStore();

  useEffect(() => {
    if (!conversationId) {
      initConversation();
    }
  }, []);

  return (
    <div className="flex flex-col h-screen w-screen bg-slate-950 text-slate-100 overflow-hidden select-none">
      <HeaderBar />
      <CacheProgressBar />

      <main className="flex-1 flex overflow-hidden">
        <ChatContainer />
        <RecursiveTreeCanvas />
      </main>

      <ValidationPanel />
    </div>
  );
};

export default App;
