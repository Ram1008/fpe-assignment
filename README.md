# AI Decision-Tree Agent

A desktop web application (`localhost:3000`) where users interact with an AI agent to build, edit, validate, and export boolean targeting decision trees for marketing campaigns, feature flags, or A/B testing.

---

## 🚀 Key Features

1. **Natural Language Interface**: Users describe targeting rules (e.g. *"Target high value customers in the US aged 25 or older"*), and the AI agent evaluates available metadata to construct the decision tree.
2. **Deterministic Decision Tree Engine**: The LLM emits structured tool calls (`ADD_SEGMENT`, `ADD_ATTRIBUTE`, `REMOVE_NODE`, `REPLACE_NODE`, `ADD_BOOLEAN_GROUP`, `REQUEST_CLARIFICATION`, `VALIDATE_TREE`, `FINISH`). Structural tree mutations are performed deterministically by the Python backend using UUID node addressing.
3. **Live Recursive Visualizer**: Displays `AND` (Sky Blue) and `OR` (Amber) boolean group containers, segment chips, and attribute predicate chips in real time, with an optional AST JSON view.
4. **Hybrid Async Bootstrapping & 24-Hour Cache**: Segment keys are discovered from paginated `/v1/users` records and cached in SQLite with a 24-hour TTL. Hot path tree building makes **0 Users API calls**. Expiry triggers incremental sync via `/v1/users/changes`.
5. **Validator-Driven Submission**: Integrates with the server-side Validator API (`/v1/validate`). Only a passing tree can be finalized, generating `final_tree.json` and `validation_report.json` in the project root directory.
6. **Persistence & App Restart Recovery**: Conversation threads, chat messages, tree AST snapshots, and metadata caches are stored in SQLite (`app_data.db`), enabling seamless app restart recovery without re-bootstrapping.
7. **Structured Observability**: Emits JSON-L event logs to `events.log` with `trace_id`, `latency_ms`, and `cache_hit` for full execution traceability.

---

## 🏗️ System Architecture

```
+---------------------------------------------------------------------------------------+
|                                    React Desktop UI                                   |
|   +-----------------------+   +----------------------------+   +------------------+   |
|   |    Chat Interface     |   | Live Tree Visualizer (Tree)|   | Validation Panel |   |
|   +-----------------------+   +----------------------------+   +------------------+   |
+-------------------------------------------|-------------------------------------------+
                                            | REST API (HTTP)
+-------------------------------------------v-------------------------------------------+
|                                  FastAPI Backend Server                               |
|   +-------------------+   +-------------------+   +--------------------+              |
|   | Agent Orchestrator|   | Decision Tree     |   | Cache Service      |              |
|   | (Anthropic SDK)   |   | Engine            |   | (24h TTL + Sync)   |              |
|   +-------------------+   +-------------------+   +--------------------+              |
|                                       |                                               |
|   +-----------------------------------v-------------------------------------------+   |
|   |                     Persistence Service (SQLite app_data.db)                  |   |
|   +-------------------------------------------------------------------------------+   |
+-------------------------------------------|-------------------------------------------+
                                            | Outbound HTTP Requests (httpx)
+-------------------------------------------v-------------------------------------------+
|  Users API (/v1/users) | Attributes API (/v1/attributes) | Validator API (/v1/validate)|
+---------------------------------------------------------------------------------------+
```

---

## 🛠️ Quick Start & Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Bearer Token & Anthropic API Key (optional fallback heuristic included)

### Installation
```bash
make install
```

### Configuration
Copy `.env.example` to `.env` and fill in your API tokens:
```bash
cp .env.example .env
```
Edit `.env`:
```env
BEARER_TOKEN=
OPEN_ROUTER_API_KEY= 
BASE_API_URL=https://dt-agent-support.divyanshgolyan.workers.dev
```

### Running the Application
Launch both backend and frontend development servers concurrently:
```bash
make run
```
Access the application in your browser at: **`http://localhost:3000`**

---

## 🧪 Running Automated Tests

Run the full automated test suite (backend pytest suite + frontend build validation):
```bash
make test
```

---

## 📁 Repository Structure

```
.
├── DESIGN.md                 # Alias pointing to design.md
├── Makefile                  # Build, run, test automation harness
├── README.md                 # Project documentation
├── backend_design.md         # Detailed backend design specification
├── design.md                 # Master architecture design specification
├── frontend_design.md        # Detailed frontend design specification
├── run_dev.py                # Dual process launcher
├── backend/
│   ├── app/
│   │   ├── api/              # REST controllers (conversations, validation, cache)
│   │   ├── domain/           # Domain models, TreeEngine, ValidatorSerializer
│   │   ├── services/         # Cache, Persistence, Orchestrator, External API clients
│   │   ├── observability/    # JSON-L events.log logger
│   │   └── main.py           # FastAPI entrypoint
│   ├── tests/                # Pytest test suite
│   └── requirements.txt      # Python dependencies
└── frontend/
    ├── src/
    │   ├── components/       # UI components (Tree visualizer, Chat, Validation)
    │   ├── store/            # Zustand stores (useChatStore, useTreeStore, etc.)
    │   └── types/            # TypeScript interfaces
    ├── package.json          # Frontend dependencies
    └── vite.config.ts        # Vite configuration & proxy settings
```
