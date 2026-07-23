# Backend Architectural & Technical Design Document (backend_design.md)

**Project Name:** AI Decision-Tree Agent (Backend)  
**Target Platform:** Python 3.11+ / FastAPI Server  
**Tech Stack:** FastAPI, Pydantic v2, OpenRouter API (`httpx`), Anthropic SDK (`anthropic`), SQLite (`sqlite3` / `aiosqlite`), Pytest  

---

## 1. Overview & Service Boundaries

The backend service is a deterministic Python/FastAPI server responsible for orchestrating conversation state, executing Multi-LLM reasoning calls (OpenRouter / Anthropic / OpenAI / Heuristic Fallback), mutating decision trees via the `TreeEngine`, maintaining SQLite persistence, managing a 24-hour API metadata cache, and communicating with external APIs (`Users`, `Attributes`, `Validator`).

### Core Design Goal
The backend guarantees that **LLM outputs never directly mutate application state**. The LLM is restricted to emitting validated `AgentAction` objects (via Tool Use). The backend `TreeEngine` validates these actions against cached metadata and applies exact structural mutations, clamping values like `account_age_days <= 10000` to satisfy server-side validator constraints.

---

## 2. Directory Structure & Module Layout

```
backend/
├── app/
│   ├── main.py                    # FastAPI entrypoint, middleware, CORS setup
│   ├── config.py                  # Pydantic BaseSettings (.env variables, API tokens, .strip())
│   ├── api/                       # REST Routers
│   │   ├── conversations.py       # Chat & state management endpoints
│   │   ├── validation.py          # Tree validation & export endpoints
│   │   └── cache.py               # Cache status & trigger refresh endpoints
│   ├── domain/                    # Core Domain & Tree Logic (Pure Python)
│   │   ├── tree_engine.py         # TreeEngine AST class & mutation operations
│   │   ├── models.py              # Pydantic schemas (TreeNode, AgentAction, etc.)
│   │   └── validator_serializer.py# Transforms internal tree AST to Validator JSON
│   ├── services/                  # Business Logic Services
│   │   ├── agent_orchestrator.py  # Multi-LLM provider orchestrator (OpenRouter/Claude/OpenAI)
│   │   ├── conversation_service.py# Session & message management
│   │   ├── cache_service.py       # TTL 24h caching manager & SQLite sync
│   │   ├── persistence_service.py # SQLite connection & transaction manager
│   │   └── external/              # External HTTP API Clients (httpx)
│   │       ├── users_client.py    # Users API discoverer (/v1/users)
│   │       ├── attributes_client.py# Attributes API fetcher (/v1/attributes)
│   │       └── validator_client.py # Validator API client (/v1/validate)
│   └── observability/
│       ├── logger.py              # Structured JSON-L logger (trace_id, latency_ms)
│       └── metrics.py             # Cache hit & API call counters
└── tests/                         # Pytest test suite
    ├── test_tree_engine.py
    ├── test_cache_service.py
    ├── test_agent_orchestrator.py
    └── test_api_routes.py
```

---

## 3. Pydantic Domain Schemas (`app/domain/models.py`)

```python
from enum import Enum
from typing import List, Union, Optional, Any, Literal
from pydantic import BaseModel, Field

class NodeType(str, Enum):
    SEGMENT = "segment"
    ATTRIBUTE = "attribute"
    AND = "AND"
    OR = "OR"

class BaseNodeModel(BaseModel):
    id: str = Field(..., description="Unique node tracking UUID")
    type: NodeType

class SegmentNodeModel(BaseNodeModel):
    type: Literal[NodeType.SEGMENT] = NodeType.SEGMENT
    key: str

class AttributeNodeModel(BaseNodeModel):
    type: Literal[NodeType.ATTRIBUTE] = NodeType.ATTRIBUTE
    attribute: str
    operator: str
    value: Union[str, int, float, bool, List[Union[str, int, float]]]

class BooleanNodeModel(BaseNodeModel):
    type: Union[Literal[NodeType.AND], Literal[NodeType.OR]]
    children: List[Union[SegmentNodeModel, AttributeNodeModel, "BooleanNodeModel"]]

TreeNodeModel = Union[SegmentNodeModel, AttributeNodeModel, BooleanNodeModel]
BooleanNodeModel.model_rebuild()

# Agent Action Tool Models
class ActionType(str, Enum):
    ADD_SEGMENT = "ADD_SEGMENT"
    ADD_ATTRIBUTE = "ADD_ATTRIBUTE"
    REMOVE_NODE = "REMOVE_NODE"
    REPLACE_NODE = "REPLACE_NODE"
    ADD_BOOLEAN_GROUP = "ADD_BOOLEAN_GROUP"
    REQUEST_CLARIFICATION = "REQUEST_CLARIFICATION"
    VALIDATE_TREE = "VALIDATE_TREE"
    FINISH = "FINISH"

class AgentActionPayload(BaseModel):
    target_parent_id: Optional[str] = None
    target_node_id: Optional[str] = None
    segment_key: Optional[str] = None
    attribute: Optional[str] = None
    operator: Optional[str] = None
    value: Optional[Any] = None
    group_type: Optional[Literal["AND", "OR"]] = None
    question: Optional[str] = None
    options: Optional[List[str]] = None
    reasoning: Optional[str] = None

class AgentAction(BaseModel):
    action: ActionType
    payload: AgentActionPayload
```

---

## 4. Decision Tree Engine (`app/domain/tree_engine.py`)

The `TreeEngine` is a stateful Python class governing AST modifications.

```python
import uuid
from typing import Optional, List, Dict
from app.domain.models import (
    TreeNodeModel, BooleanNodeModel, SegmentNodeModel, AttributeNodeModel, NodeType
)

class TreeEngine:
    def __init__(self, root: Optional[TreeNodeModel] = None):
        if root is None:
            # Default root is an OR group
            self.root = BooleanNodeModel(id=f"node_{uuid.uuid4().hex[:8]}", type=NodeType.OR, children=[])
        else:
            self.root = root

    def add_segment(self, segment_key: str, parent_id: Optional[str] = None) -> SegmentNodeModel:
        new_node = SegmentNodeModel(id=f"node_{uuid.uuid4().hex[:8]}", key=segment_key)
        target = self.find_node(parent_id) if parent_id else self.root
        if isinstance(target, BooleanNodeModel):
            target.children.append(new_node)
        else:
            # If target is a leaf, wrap target & new_node in an AND group
            parent = self.find_parent(target.id)
            new_group = BooleanNodeModel(
                id=f"node_{uuid.uuid4().hex[:8]}",
                type=NodeType.AND,
                children=[target, new_node]
            )
            self._replace_child(parent, target.id, new_group)
        return new_node

    def add_attribute(self, attribute: str, operator: str, value: any, parent_id: Optional[str] = None) -> AttributeNodeModel:
        new_node = AttributeNodeModel(
            id=f"node_{uuid.uuid4().hex[:8]}",
            attribute=attribute,
            operator=operator,
            value=value
        )
        target = self.find_node(parent_id) if parent_id else self.root
        if isinstance(target, BooleanNodeModel):
            target.children.append(new_node)
        return new_node

    def remove_node(self, node_id: str) -> bool:
        if self.root.id == node_id:
            # Reset to empty root
            self.root = BooleanNodeModel(id=f"node_{uuid.uuid4().hex[:8]}", type=NodeType.OR, children=[])
            return True
        parent = self.find_parent(node_id)
        if parent and isinstance(parent, BooleanNodeModel):
            parent.children = [c for c in parent.children if c.id != node_id]
            self._prune_empty_groups(self.root)
            return True
        return False

    def serialize_for_validator(self) -> Dict:
        def _strip_ids(node: TreeNodeModel) -> Dict:
            if node.type in [NodeType.AND, NodeType.OR]:
                return {
                    "type": node.type.value,
                    "children": [_strip_ids(c) for c in node.children]
                }
            elif node.type == NodeType.SEGMENT:
                return {"type": "segment", "key": node.key}
            else:
                return {
                    "type": "attribute",
                    "attribute": node.attribute,
                    "operator": node.operator,
                    "value": node.value
                }
        return _strip_ids(self.root)
```

---

## 5. Cache & Discovery Architecture (`app/services/cache_service.py`)

### Hybrid Async Bootstrapping & Incremental Sync Strategy
1. **Startup Check**: Upon FastAPI server startup, `CacheService` inspects SQLite `metadata_cache` for `discovered_segments` and `attribute_schema`.
2. **Valid TTL Flow**: If cache exists and `fetched_at + 24 hours > current_time`:
   - `CacheStatus = READY`.
   - Building trees on the hot path generates **0 Users API calls**.
3. **Missing / Expired Cache Flow (Hybrid Async)**:
   - If cache does not exist, `CacheStatus = BOOTSTRAPPING`.
   - An asynchronous background asyncio task is spawned immediately so FastAPI server start is not blocked.
   - The UI displays a cache bootstrap progress bar while background discovery runs.
   - If cache exists but TTL is expired (> 24h), `CacheService` performs **incremental synchronization** by querying `/v1/users/changes?since=<last_sync_timestamp>` instead of re-crawling all users, conserving rate limits and bandwidth.
4. **Attributes Discovery**:
   - `AttributesService` fetches `/v1/attributes` and updates attribute schema dictionary in SQLite cache.

---

## 6. Prompt Engineering & Multi-LLM Provider Cascade

The `AgentOrchestrator` implements a priority routing cascade:
1. **OpenRouter API Gateway**: Recommended primary provider using `openai/gpt-4o-mini`.
2. **Anthropic Claude API**: Direct SDK provider (`claude-3-5-sonnet`).
3. **OpenAI-Compatible API**: Direct REST API endpoint provider.
4. **Deterministic Heuristic Engine**: Offline fallback engine for local offline testing.

### Header & Tool Payload Safety Features:
- **String Sanitization**: All API keys and authorization headers are passed through `.strip()` to prevent HTTP header validation errors caused by trailing newlines in `.env`.
- **Dual Format Payload Parsing**: Tool argument parser accepts both nested payload schemas (`args["payload"]`) and flat payload schemas (`args["attribute"]`, `args["segment_key"]`).
- **Value Boundary Safety**: Prompt Directive 5 enforces `account_age_days <= 10000` clamping to satisfy server-side validator limits.

### System Prompt Structure

```markdown
You are an expert AI Decision-Tree Agent constructing audience targeting boolean logic.

STRICT OPERATIONAL DIRECTIVES:
1. You DO NOT mutate application state directly. You MUST call tools (Agent Actions) to edit the decision tree.
2. Available Segments: {known_segments_list}
3. Available Attributes & Operators: {known_attributes_json}
4. Current Decision Tree: {current_tree_json}
5. Value Boundaries: Attribute `account_age_days` MUST NOT exceed 10000. Clamp values if user specifies years (> 10000 days).

RULES:
- If a user asks for an ambiguous segment (e.g. "recent buyers"), call tool `REQUEST_CLARIFICATION` asking for clarification.
- If a user requests a segment or attribute not in the available catalog, call tool `REQUEST_CLARIFICATION` pushing back and suggesting alternatives.
```

### Anthropic Tool Definition

```python
AGENT_TOOLS = [
    {
        "name": "execute_agent_action",
        "description": "Mutate the targeting decision tree or request clarification",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "ADD_SEGMENT", "ADD_ATTRIBUTE", "REMOVE_NODE",
                        "REPLACE_NODE", "ADD_BOOLEAN_GROUP",
                        "REQUEST_CLARIFICATION", "VALIDATE_TREE", "FINISH"
                    ]
                },
                "payload": {
                    "type": "object",
                    "properties": {
                        "segment_key": {"type": "string"},
                        "attribute": {"type": "string"},
                        "operator": {"type": "string"},
                        "value": {"type": "string"},
                        "group_type": {"type": "string", "enum": ["AND", "OR"]},
                        "question": {"type": "string"},
                        "reasoning": {"type": "string"}
                    }
                }
            },
            "required": ["action", "payload"]
        }
    }
]
```

---

## 7. REST API Endpoints Specification

### 1. `POST /api/conversations`
Creates a new conversation session.
- **Response**: `{ "conversation_id": "conv_123", "tree": { ... } }`

### 2. `POST /api/conversations/{id}/messages`
Sends user prompt, triggers LLM agent turn, executes tree mutations, and returns response.
- **Request**: `{ "content": "Target high value customers in the US" }`
- **Response**:
  ```json
  {
    "message_id": "msg_456",
    "agent_response": "Added segment 'high_value_customers' and attribute 'country == US'.",
    "actions_taken": [...],
    "tree": { ... },
    "validation_status": { "ok": true }
  }
  ```

### 3. `POST /api/conversations/{id}/validate`
Triggers external Validator API (`/v1/validate`).
- **Response**: `{ "ok": true, "errors": [], "warnings": [] }`

### 4. `POST /api/conversations/{id}/submit`
Finalizes tree. Writes `final_tree.json` and `validation_report.json` to project root directory.

---

## 8. Observability & JSON-L Logging

Structured log entries are appended to `events.log`:

```json
{"timestamp": "2026-07-22T01:45:00Z", "trace_id": "tr_991823", "event": "llm_agent_turn", "latency_ms": 412, "cache_hit": true, "action": "ADD_SEGMENT", "segment_key": "high_value_customers"}
```

---

## 9. Backend Verification & Test Plan

- **`test_tree_engine.py`**: Validates AST insertions, removals, nested boolean grouping, and validator serialization.
- **`test_cache_service.py`**: Verifies 24-hour TTL expiration, SQLite persistence, and 0 Users API call enforcement.
- **`test_agent_orchestrator.py`**: Mocks Anthropic Tool Use responses and verifies pushback logic on unknown attributes.
- **`test_api_routes.py`**: FastAPI TestClient integration testing complete message turn through validation and submit.
