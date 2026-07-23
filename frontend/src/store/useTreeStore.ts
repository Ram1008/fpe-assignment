import { create } from 'zustand';
import { TreeNode } from '../types';

interface TreeStore {
  tree: TreeNode | null;
  selectedNodeId: string | null;
  setTree: (newTree: TreeNode) => void;
  setSelectedNodeId: (id: string | null) => void;
  clearTree: () => void;
}

export const useTreeStore = create<TreeStore>((set) => ({
  tree: null,
  selectedNodeId: null,
  setTree: (newTree: TreeNode) => set({ tree: newTree }),
  setSelectedNodeId: (id: string | null) => set({ selectedNodeId: id }),
  clearTree: () => set({ tree: null, selectedNodeId: null }),
}));
