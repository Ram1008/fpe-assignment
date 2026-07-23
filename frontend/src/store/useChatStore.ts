import { create } from 'zustand';
import axios from 'axios';
import { ChatMessage } from '../types';
import { useTreeStore } from './useTreeStore';
import { useValidationStore } from './useValidationStore';

interface PendingClarification {
  question: string;
  options?: string[];
}

interface ChatStore {
  conversationId: string | null;
  conversationsList: Array<{ id: string; title: string; created_at: string }>;
  messages: ChatMessage[];
  isAgentThinking: boolean;
  pendingClarification: PendingClarification | null;
  initConversation: () => Promise<void>;
  loadConversation: (id: string) => Promise<void>;
  sendMessage: (text: string) => Promise<void>;
  submitClarification: (answer: string) => Promise<void>;
  fetchConversationsList: () => Promise<void>;
}

export const useChatStore = create<ChatStore>((set, get) => ({
  conversationId: null,
  conversationsList: [],
  messages: [],
  isAgentThinking: false,
  pendingClarification: null,

  fetchConversationsList: async () => {
    try {
      const resp = await axios.get('/api/conversations');
      set({ conversationsList: resp.data });
    } catch (e) {
      console.error('Error fetching conversations list:', e);
    }
  },

  initConversation: async () => {
    try {
      const resp = await axios.post('/api/conversations', { title: 'Audience Targeting Session' });
      const { conversation_id, tree } = resp.data;
      set({
        conversationId: conversation_id,
        messages: [
          {
            id: 'msg_welcome',
            sender: 'agent',
            content: 'Hello! I am your AI Decision-Tree Agent. Describe your targeting goal (e.g., "Target high value customers in the US aged 25 or older").',
            created_at: new Date().toISOString(),
          },
        ],
        pendingClarification: null,
      });
      useTreeStore.getState().setTree(tree);
      get().fetchConversationsList();
    } catch (e) {
      console.error('Failed to init conversation:', e);
    }
  },

  loadConversation: async (id: string) => {
    try {
      set({ isAgentThinking: true });
      const resp = await axios.get(`/api/conversations/${id}`);
      const { conversation_id, messages, tree_snapshot } = resp.data;
      set({
        conversationId: conversation_id,
        messages: messages || [],
        pendingClarification: null,
        isAgentThinking: false,
      });
      if (tree_snapshot && tree_snapshot.tree) {
        useTreeStore.getState().setTree(tree_snapshot.tree);
        if (tree_snapshot.validation_report) {
          useValidationStore.getState().setValidationReport(tree_snapshot.validation_report);
        }
      }
    } catch (e) {
      console.error('Failed to load conversation:', e);
      set({ isAgentThinking: false });
    }
  },

  sendMessage: async (text: string) => {
    const { conversationId, messages } = get();
    if (!conversationId || !text.trim()) return;

    const userMsg: ChatMessage = {
      id: `user_${Date.now()}`,
      sender: 'user',
      content: text,
      created_at: new Date().toISOString(),
    };

    set({
      messages: [...messages, userMsg],
      isAgentThinking: true,
      pendingClarification: null,
    });

    try {
      const resp = await axios.post(`/api/conversations/${conversationId}/messages`, { content: text });
      const { agent_response, tree, validation_report, pending_clarification, actions_taken } = resp.data;

      const agentMsg: ChatMessage = {
        id: `agent_${Date.now()}`,
        sender: 'agent',
        content: agent_response,
        action_json: actions_taken,
        created_at: new Date().toISOString(),
      };

      set((state) => ({
        messages: [...state.messages, agentMsg],
        isAgentThinking: false,
        pendingClarification: pending_clarification || null,
      }));

      if (tree) {
        useTreeStore.getState().setTree(tree);
      }
      if (validation_report) {
        useValidationStore.getState().setValidationReport(validation_report);
      }
    } catch (e: any) {
      console.error('Send message error:', e);
      const errMsg: ChatMessage = {
        id: `err_${Date.now()}`,
        sender: 'system',
        content: `Error: ${e.response?.data?.detail || e.message}`,
        created_at: new Date().toISOString(),
      };
      set((state) => ({
        messages: [...state.messages, errMsg],
        isAgentThinking: false,
      }));
    }
  },

  submitClarification: async (answer: string) => {
    set({ pendingClarification: null });
    await get().sendMessage(answer);
  },
}));
