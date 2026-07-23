export type NodeType = 'segment' | 'attribute' | 'AND' | 'OR';

export interface BaseNode {
  id: string;
  type: NodeType;
}

export interface SegmentNode extends BaseNode {
  type: 'segment';
  key: string;
}

export interface AttributeNode extends BaseNode {
  type: 'attribute';
  attribute: string;
  operator: string;
  value: any;
}

export interface BooleanNode extends BaseNode {
  type: 'AND' | 'OR';
  children: TreeNode[];
}

export type TreeNode = SegmentNode | AttributeNode | BooleanNode;

export interface ChatMessage {
  id: string;
  sender: 'user' | 'agent' | 'system';
  content: string;
  action_json?: any;
  created_at: string;
}

export interface ValidationReport {
  ok: boolean;
  errors?: Array<{ path: string; code: string; message: string }>;
  warnings?: string[];
}

export interface CacheStatus {
  status: 'READY' | 'BOOTSTRAPPING' | 'EXPIRED' | 'UNINITIALIZED';
  is_bootstrapping: boolean;
  segments_count: number;
  segments_cache_timestamp: string | null;
  attributes_count: number;
  last_error?: string | null;
}
