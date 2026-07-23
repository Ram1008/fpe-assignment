import { create } from 'zustand';
import axios from 'axios';
import { CacheStatus } from '../types';

interface CacheStore {
  cacheStatus: CacheStatus | null;
  fetchStatus: () => Promise<void>;
  triggerRefresh: () => Promise<void>;
}

export const useCacheStore = create<CacheStore>((set) => ({
  cacheStatus: null,

  fetchStatus: async () => {
    try {
      const resp = await axios.get('/api/cache/status');
      set({ cacheStatus: resp.data });
    } catch (e) {
      console.error('Failed to fetch cache status:', e);
    }
  },

  triggerRefresh: async () => {
    try {
      await axios.post('/api/cache/refresh');
      const resp = await axios.get('/api/cache/status');
      set({ cacheStatus: resp.data });
    } catch (e) {
      console.error('Failed to trigger cache refresh:', e);
    }
  },
}));
