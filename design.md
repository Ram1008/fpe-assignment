# System Architecture & Technical Design Document (design.md)

**Project Name:** AI Decision-Tree Agent  
**Target Platform:** Desktop Web Application (`localhost:3000`)  
**Document Version:** 1.0.0  
**Target Audience:** Human Engineers & Autonomous AI Verification Agents  

---

## 1. Executive Summary & Project Goal

The **AI Decision-Tree Agent** is a desktop web application enabling users to construct, edit, validate, and finalize boolean targeting decision trees for marketing campaigns, feature flags, and A/B test targeting via natural language interaction.

The system integrates an LLM (Anthropic Claude) with a **deterministic local Decision Tree Engine**. The LLM acts solely as a reasoning engine emitting structured actions; it does **not** maintain application state or directly mutate tree structures. All structural mutations, caching, persistence, and schema validations are performed deterministically by the Python/FastAPI backend and local tree engine.

### Key Deliverables & Artifacts
1. **Desktop Web App (`localhost:3000`)**: Interactive chat interface, live recursive decision tree visualization, cache status progress indicator, and a "Validate & Submit" workflow.
2. **Persistence & Cache**: Local SQLite storage preserving conversation history, tree revisions, and discovered metadata across application restarts. Uses hybrid async bootstrapping and incremental sync (`/v1/users/changes`).
3. **Exported Artifacts**: `final_tree.json` and `validation_report.json` emitted upon successful validation and user submit action, plus optional structured JSON-L logs (`events.log`).

---

## 2. Core Architectural Principles & Boundaries

1. **LLM Does Not Own Application State**: The tree state is stored in SQLite and managed in memory by a deterministic `TreeEngine`. The LLM receives the current state as context in its prompt and responds exclusively with **Agent Actions** (Tool Calls / Structured JSON). Node mutation targets strictly use UUID-based `node_id`.
2. **Deterministic Tree Mutations**: All additions, replacements, deletions, and boolean groupings are executed by the `TreeEngine` Python class with strict type checks and UUID node addressing.
3. **Cache-First Architecture & Hybrid Async Bootstrapping**:
   - Attribute definitions (`/v1/attributes`) and discovered segment keys (`/v1/users`) are cached in SQLite with a 24-hour TTL.
   - On startup, if a valid cache exists, server starts immediately (**0 Users API requests**).
   - If cache is missing or expired, a background task initiates discovery, setting `Cache Status = BOOTSTRAPPING` while the UI displays loading progress.
   - Cache refresh uses incremental synchronization via `/v1/users/changes?since=<last_timestamp>` to optimize bandwidth.
4. **Validator-Driven Finalization**: A tree cannot be marked final or exported until the server-side `/v1/validate` API responds with `ok: true`.
5. **Restart Recovery**: Killing and restarting the server allows instant resumption of ongoing conversations and tree state without re-bootstrapping metadata if TTL is valid.

---

## 3. System Architecture Diagram

```
+---------------------------------------------------------------------------------------+
|                                    React Desktop UI                                   |
|   +-----------------------+   +----------------------------+   +------------------+   |
|   |    Chat Interface     |   | Live Tree Visualizer (Tree)|   | Validation Panel |   |
|   +-----------------------+   +----------------------------+   +------------------+   |
+-------------------------------------------|-------------------------------------------+
                                            | REST API / Event Stream (HTTP)
+-------------------------------------------v-------------------------------------------+
|                                  FastAPI Backend Server                               |
|                                                                                       |
|   +-------------------------------------------------------------------------------+   |
|   |                          Conversation Manager / Orchestrator                  |   |
|   +-------------------+-----------------------+-----------------------+-----------+   |
|                       |                       |                       |               |
|                       v                       v                       v               |
|            +--------------------+   +-------------------+   +--------------------+    |
|            | Agent Orchestrator |   | Decision Tree     |   | Cache Service      |    |
|            | (Anthropic SDK)    |   | Engine            |   | (TTL 24h)          |    |
|            +--------------------+   +-------------------+   +--------------------+    |
|                                               |                       |               |
|                                               v                       |               |
|                                     +-------------------+             |               |
|                                     | Validator Service |             |               |
|                                     +-------------------+             |               |
|                                               |                       |               |
|   +-------------------------------------------v-----------------------v-----------+   |
|   |                         Persistence Service (SQLite Database)                 |   |
|   +-------------------------------------------------------------------------------+   |
+-------------------------------------------|-------------------------------------------+
                                            | Outbound HTTP Requests (httpx)
+-------------------------------------------v-------------------------------------------+
|                               External APIs & LLM Provider                            |
|  +-----------------------+    +-----------------------+    +-----------------------+  |
|  | Users API             |    | Attributes API        |    | Validator API         |  |
|  | /v1/users             |    | /v1/attributes        |    | /v1/validate          |  |
|  +-----------------------+    +-----------------------+    +-----------------------+  |
|  +---------------------------------------------------------------------------------+  |
|  | Anthropic Claude API (claude-3-5-sonnet / tool_use)                             |  |
|  +---------------------------------------------------------------------------------+  |
+---------------------------------------------------------------------------------------+
```

---

## 4. Detailed Data Models & Specifications

### 4.1 Internal Tree Model vs. Validator API Payload

The tree engine maintains an internal node representation with unique `id` trackers for precise UI rendering and targeted LLM action replacement. When validating or exporting, it serializes to the exact schema expected by `/v1/validate`.

#### Internal Data Models (Python / TypeScript Pydantic & TS Interfaces)

```typescript
// Node Types
export type NodeType = 'segment' | 'attribute' | 'AND' | 'OR';

// Node ID format: node_uuid_v4
export interface BaseNode {
  id: string;
  type: NodeType;
}

export interface SegmentNode extends BaseNode {
  type: 'segment';
  key: string; // e.g., "high_value_customers"
}

export interface AttributePredicateNode extends BaseNode {
  type: 'attribute';
  attribute: string; // e.g., "age"
  operator: '>=' | '<=' | '==' | '!=' | '>' | '<' | 'in' | 'contains';
  value: string | number | boolean | Array<string | number>;
}

export interface BooleanGroupNode extends BaseNode {
  type: 'AND' | 'OR';
  children: TreeNode[];
}

export type TreeNode = SegmentNode | AttributePredicateNode | BooleanGroupNode;
```

#### Serialized Validator Payload Schema (Output for `/v1/validate`)

```json
{
  "tree": {
    "type": "OR",
    "children": [
      {
        "type": "segment",
        "key": "high_value_customers"
      },
      {
        "type": "AND",
        "children": [
          {
            "type": "attribute",
            "attribute": "age",
            "operator": ">=",
            "value": 25
          },
          {
            "type": "attribute",
            "attribute": "country",
            "operator": "==",
            "value": "US"
          }
        ]
      }
    ]
  },
  "segments_cache_timestamp": "2026-07-22T00:00:00Z"
}
```

---

## 5. Agent Action Protocol Specification

All natural language reasoning produces structured tool calls conforming to the **Agent Action Protocol**. The LLM emits one or more of these actions per turn.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AgentAction",
  "type": "object",
  "properties": {
    "action": {
      "type": "string",
      "enum": [
        "ADD_SEGMENT",
        "ADD_ATTRIBUTE",
        "REMOVE_NODE",
        "REPLACE_NODE",
        "ADD_BOOLEAN_GROUP",
        "REQUEST_CLARIFICATION",
        "VALIDATE_TREE",
        "FINISH"
      ]
    },
    "payload": {
      "type": "object",
      "properties": {
        "target_parent_id": { "type": ["string", "null"], "description": "ID of parent group node, defaults to root" },
        "target_node_id": { "type": "string", "description": "Target node ID for replace/remove" },
        "segment_key": { "type": "string" },
        "attribute": { "type": "string" },
        "operator": { "type": "string" },
        "value": { "type": ["string", "number", "boolean", "array"] },
        "group_type": { "type": "string", "enum": ["AND", "OR"] },
        "question": { "type": "string", "description": "Clarifying question when user input is ambiguous" },
        "options": { "type": "array", "items": { "type": "string" } },
        "reasoning": { "type": "string", "description": "Explanation of action taken" }
      }
    }
  },
  "required": ["action", "payload"]
}
```

### Action Handling Rules
1. `ADD_SEGMENT`: Verifies segment exists in cache set. If missing, triggers `REQUEST_CLARIFICATION` / Pushback.
2. `ADD_ATTRIBUTE`: Verifies attribute exists and operator is valid for type (`number`, `string`, `boolean`). Push back if invalid.
3. `REMOVE_NODE`: Removes node by `target_node_id` and prunes empty boolean parent groups.
4. `REPLACE_NODE`: Replaces node specified by `target_node_id` with new Segment or Attribute predicate.
5. `ADD_BOOLEAN_GROUP`: Wraps children under a new `AND` or `OR` group.
6. `REQUEST_CLARIFICATION`: Halts tree mutation and prompts user for ambiguous terms (e.g. "recent users" -> "How many days back?").
7. `VALIDATE_TREE`: Triggers `/v1/validate` API call and updates status panel.
8. `FINISH`: Saves `final_tree.json` and `validation_report.json`.

---

## 6. Database & Persistence Architecture (SQLite)

### SQLite Schema (`sqlite3` / `aiosqlite`)

```sql
-- Conversations Table
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Messages Table
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    sender TEXT CHECK(sender IN ('user', 'agent', 'system')) NOT NULL,
    content TEXT NOT NULL,
    action_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

-- Tree Snapshots Table (Supports undo / conversation revision history)
CREATE TABLE IF NOT EXISTS tree_snapshots (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    tree_json TEXT NOT NULL,
    is_valid BOOLEAN DEFAULT FALSE,
    validation_report TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

-- Metadata & API Cache Table
CREATE TABLE IF NOT EXISTS metadata_cache (
    cache_key TEXT PRIMARY KEY, -- 'discovered_segments', 'attribute_schema', 'users_meta'
    data_json TEXT NOT NULL,
    fetched_at TIMESTAMP NOT NULL,
    etag TEXT,
    ttl_seconds INTEGER DEFAULT 86400
);
```

---

## 7. Service Layer Architecture (Backend)

1. **`UsersService`**:
   - Fetches `/v1/users/meta` to determine total count & budgets (`max_requests_per_hour`).
   - Discovers unique segments by iterating `/v1/users` (paginated `limit=1000`).
   - Uses `ETag` / `If-None-Match` to save bandwidth.
   - Computes segment set and sets `segments_cache_timestamp`.

2. **`AttributesService`**:
   - Calls `/v1/attributes` to fetch master schema list (`id`, `type`, `ops`, `description`, `enum_values`, `min`, `max`).
   - Provides fast lookup dictionary for LLM prompt context injection and validation.

3. **`CacheService`**:
   - Manages SQLite `metadata_cache` table.
   - Evaluates TTL (`fetched_at + 24 hours > now`).
   - Exposes `is_cache_valid()`, `get_segments()`, `get_attributes()`.
   - Ensures hot path tree building makes **0 outbound API calls to Users API**.

4. **`TreeEngine`**:
   - Maintains memory representation of the AST (Abstract Syntax Tree).
   - Methods: `add_node()`, `remove_node()`, `replace_node()`, `group_nodes()`, `serialize_validator_format()`.
   - Handles auto-cleaning (removing orphan AND/OR nodes with single or zero children).

5. **`AgentOrchestrator`**:
   - Constructs dynamic system prompt injecting:
     - Available segments catalog
     - Attribute definitions & allowed operators
     - Current serialized decision tree
     - Conversation state
   - Invokes Anthropic API (`claude-3-5-sonnet`) with Tool Definitions matching Agent Actions.

6. **`ValidatorService`**:
   - POST to `/v1/validate` with tree payload and `segments_cache_timestamp`.
   - Returns `{ ok: bool, errors: [...], warnings: [...] }`.

---

## 8. Development Phases & Implementation Roadmap

```
Phase 1: Environment & Boilerplate Setup (FastAPI + React Vite + SQLite schema)
Phase 2: Core Domain Model & Tree Engine (AST definition, mutation algorithms, serialization)
Phase 3: External API Integration & Caching (UsersService, AttributesService, CacheService, ETag)
Phase 4: SQLite Persistence & Recovery Engine (Conversation state, snapshot storage, resume)
Phase 5: Agent Orchestrator & Anthropic Integration (System prompts, function tools, pushback logic)
Phase 6: REST API Controllers (Conversations, Messages, Validation endpoints)
Phase 7: Frontend Interface & Tree Visualizer (React, Zustand, Tailwind, interactive tree rendering)
Phase 8: Validation Pipeline & Artifact Exporter (Final tree generation, report saving)
Phase 9: Observability & Logging Middleware (JSON-L events.log tracer)
Phase 10: Automated Verification & Integration Testing (Pytest, Vitest, Makefile harness)
```

---

## 9. Non-Functional & Acceptance Criteria Matrix

| Criterion | Requirement | Implementation Strategy |
| :--- | :--- | :--- |
| **Hot path cache** | 0 Users API calls during tree building | `CacheService` stores discovered segment set with 24h TTL; check TTL before any fetch |
| **Clarify on miss** | Unknown segment triggers helpful error | `AgentOrchestrator` validates proposed segment against cache before tree modification |
| **Attribute correctness**| Pushback on invalid type or operator | `TreeEngine` / `AttributesService` validates operator against attribute data type |
| **Restart/resume** | App kill preserves state without re-bootstrap| SQLite `tree_snapshots` and `metadata_cache` checked on server startup |
| **Validator pass** | Export only after Validator API returns `ok: true` | Frontend submit button disabled until `/v1/validate` returns `ok: true` |
| **Reproducibility** | Standard build execution | `Makefile` providing `make run` and `make test` |
