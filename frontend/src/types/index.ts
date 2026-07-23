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
  errors?: Array<{ path: string; code: string; message: string; actionable_recommendation?: string }>;
  warnings?: string[];
  summary?: {
    status: string;
    validated_at: string;
    validator_service: string;
    segments_cache_timestamp: string;
    ast_metrics?: {
      total_nodes: number;
      tree_depth: number;
      node_counts: {
        boolean_groups: { OR: number; AND: number; total: number };
        segments: number;
        attributes: number;
      };
    };
  };
  structure_analysis?: any;
  diagnostics?: {
    errors_count: number;
    errors: Array<{ path: string; code: string; message: string; actionable_recommendation?: string }>;
    warnings_count: number;
    warnings: string[];
  };
  recommendations_and_insights?: Array<{
    category: string;
    level: string;
    title: string;
    details: string;
  }>;
}

export interface CacheStatus {
  status: 'READY' | 'BOOTSTRAPPING' | 'EXPIRED' | 'UNINITIALIZED';
  is_bootstrapping: boolean;
  segments_count: number;
  segments_cache_timestamp: string | null;
  attributes_count: number;
  last_error?: string | null;
}
