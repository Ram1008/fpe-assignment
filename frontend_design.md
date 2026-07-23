# Frontend Architectural & Technical Design Document (frontend_design.md)

**Project Name:** AI Decision-Tree Agent (Frontend)  
**Target Platform:** Desktop Web Application (`localhost:3000`)  
**Tech Stack:** React 18, TypeScript, Vite, Zustand, Tailwind CSS, Lucide Icons  

---

## 1. Overview & UI Objectives

The frontend application provides a sleek, modern, desktop-optimized web workspace where users interact with an AI Decision-Tree Agent. It visualizes the boolean decision tree in real-time as natural language instructions are processed.

### Key UI Features
1. **Interactive Chat & Copy Panel**: Full conversational history with message bubbles, agent action badges (`ADD_SEGMENT`, `ADD_ATTRIBUTE`, etc.), clarifying question dialogs, and a top-bar **Copy Chat** control to copy complete thread transcripts or single messages to clipboard.
2. **Live Decision Tree Visualizer**: Recursive component rendering boolean operators (`AND` Sky Blue, `OR` Amber), segment cards (Emerald), and attribute predicate cards (Purple) with interactive controls (edit, delete, re-order).
3. **Validation & Submission Bar**: Displays real-time validator readiness, error/warning diagnostics from `/v1/validate`, and a single-click "Validate & Export" button emitting `final_tree.json` and `validation_report.json`.
4. **Session History Drawer & Cache Badge**: Live 24h TTL cache status badge with manual refresh button, session switcher, and new tree initializer.

---

## 2. Component Architecture & Hierarchy

```
AppShell (Layout Wrapper)
├── HeaderBar (App title, API status, Cache TTL indicator, Session switcher)
├── MainWorkspace (Grid Layout: 440px Chat / Flex Tree Preview)
│   ├── ChatContainer
│   │   ├── ChatHeaderBar (Title, msg counter, Copy Chat button)
│   │   ├── MessageList
│   │   │   ├── UserMessageBubble (Copy button on hover)
│   │   │   ├── AgentMessageBubble (Markdown render + Action Tag + Copy button)
│   │   │   └── ClarificationModal (Select options / Type answer)
│   │   └── ChatInputArea (Textarea + Send Button + Quick Prompts)
│   └── TreePreviewPanel
│       ├── RecursiveTreeCanvas (Renders root BooleanNode)
│       │   └── TreeNodeComponent (Recursive)
│       │       ├── BooleanGroupCard (AND / OR with color codes)
│       │       ├── SegmentChip (Badge + segment metadata tooltip)
│       │       └── AttributeChip (Attribute name + operator + value)
│       └── ValidationFooterPanel
│           ├── StatusBadge (Valid / Invalid / Pending)
│           ├── ErrorWarningList (Expandable drawer showing paths & messages)
│           └── SubmitExportButton (Triggers final_tree.json export)
```

---

## 3. Zustand State Management Architecture

The frontend state is partitioned into clean, decoupled Zustand stores.

```typescript
// 1. useChatStore - Manages active conversation and messages
interface ChatMessage {
  id: string;
  sender: 'user' | 'agent' | 'system';
  content: string;
  actionsPerformed?: AgentAction[];
  timestamp: string;
}

interface ChatStore {
  conversationId: string | null;
  messages: ChatMessage[];
  isAgentThinking: boolean;
  pendingClarification: {
    question: string;
    options?: string[];
  } | null;
  sendMessage: (text: string) => Promise<void>;
  submitClarification: (answer: string) => Promise<void>;
  loadConversation: (id: string) => Promise<void>;
}

// 2. useTreeStore - Manages decision tree AST and UI mutations
interface TreeStore {
  tree: TreeNode | null;
  selectedNodeId: string | null;
  setTree: (newTree: TreeNode) => void;
  removeNode: (nodeId: string) => void;
  updateNode: (nodeId: string, updated: TreeNode) => void;
  clearTree: () => void;
}

// 3. useValidationStore - Manages validation status and exports
interface ValidationResult {
  ok: boolean;
  errors: Array<{ path: string; code: string; message: string }>;
  warnings: string[];
}

interface ValidationStore {
  isValidating: boolean;
  validationReport: ValidationResult | null;
  segmentsCacheTimestamp: string | null;
  validateTree: () => Promise<void>;
  exportFinalTree: () => Promise<void>;
}
```

---

## 4. Visual Design System & Aesthetics

- **Color Palette (Sleek Dark / Slate Theme)**:
  - Background: `#0f172a` (Slate 900)
  - Surface Containers: `#1e293b` (Slate 800) with subtle backdrop blur (Glassmorphism)
  - Primary Accent: `#6366f1` (Indigo 500)
  - Boolean `AND` Group: `#0284c7` (Sky 600 border with gradient background)
  - Boolean `OR` Group: `#d97706` (Amber 600 border with gradient background)
  - Segment Node: `#10b981` (Emerald 500 chip)
  - Attribute Node: `#8b5cf6` (Purple 500 chip)
  - Error Accent: `#ef4444` (Red 500)
- **Typography**: Inter / Outfit via Google Fonts.
- **Animations**: Framer Motion for smooth tree expansion, node addition pop-ins, and message bubble transitions.

---

## 5. Recursive Tree Component Design Specification

The core component `TreeNodeComponent.tsx` recursively inspects the `node.type` and renders nested structures:

```tsx
export const TreeNodeComponent: React.FC<{ node: TreeNode; depth?: number }> = ({ node, depth = 0 }) => {
  if (node.type === 'AND' || node.type === 'OR') {
    return (
      <div className={`p-4 rounded-xl border-2 ${node.type === 'AND' ? 'border-sky-500 bg-sky-950/20' : 'border-amber-500 bg-amber-950/20'} my-2`}>
        <div className="flex items-center gap-2 mb-2 font-bold">
          <span className={`px-2 py-1 rounded text-xs text-white ${node.type === 'AND' ? 'bg-sky-600' : 'bg-amber-600'}`}>
            {node.type}
          </span>
          <span className="text-xs text-slate-400">({node.children.length} conditions)</span>
        </div>
        <div className="pl-4 border-l-2 border-slate-700 space-y-2">
          {node.children.map((childNode) => (
            <TreeNodeComponent key={childNode.id} node={childNode} depth={depth + 1} />
          ))}
        </div>
      </div>
    );
  }

  if (node.type === 'segment') {
    return (
      <div className="flex items-center gap-2 p-2 bg-emerald-950/40 border border-emerald-500/50 rounded-lg text-emerald-300">
        <TagIcon className="w-4 h-4 text-emerald-400" />
        <span className="font-mono text-sm font-semibold">{node.key}</span>
      </div>
    );
  }

  // Attribute Node
  return (
    <div className="flex items-center gap-2 p-2 bg-purple-950/40 border border-purple-500/50 rounded-lg text-purple-300">
      <SlidersIcon className="w-4 h-4 text-purple-400" />
      <span className="font-mono text-sm">{node.attribute}</span>
      <span className="font-bold text-xs bg-purple-800 px-1.5 py-0.5 rounded">{node.operator}</span>
      <span className="font-mono text-sm font-semibold">{JSON.stringify(node.value)}</span>
    </div>
  );
};
```

---

## 6. Interaction Workflows & Error Pushback

1. **Clarification Handling**: When the backend agent emits `REQUEST_CLARIFICATION`, the chat UI renders an interactive option selector or question callout, pausing input until answered.
2. **Invalid Segment / Attribute Pushback**: If the user asks for `"unknown_segment"`, the backend returns an error message with suggested alternative segments. The UI highlights suggested chips in the agent bubble that can be clicked to apply.
3. **Live Validation Feedback**: Whenever the tree modifies, an asynchronous validation check runs in the background against `/api/conversations/{id}/validate`. If errors exist, red inline badges appear on the affected tree nodes matching the error JSON `path`.

---

## 7. Frontend Verification Strategy

- **Unit Testing**: Vitest & React Testing Library for `TreeNodeComponent`, `ChatInputArea`, and Zustand store logic.
- **Visual Regression**: Mock tree structures passed to `TreeNodeComponent` to verify correct nested styling for deep tree structures.
- **End-to-End Test**: Cypress or Playwright test replicating: User enters prompt -> Agent adds segment -> Visualizer updates -> User validates -> Download triggered.
