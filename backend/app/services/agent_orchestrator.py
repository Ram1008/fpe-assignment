import os
import sys
import json
import httpx
from typing import Dict, Any, List, Optional

# Ensure backend root is in sys.path
_backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

import anthropic
from app.config import settings
from app.domain.models import AgentAction, ActionType, AgentActionPayload

# 1. Anthropic Tool Schema
ANTHROPIC_TOOLS = [
    {
        "name": "execute_agent_action",
        "description": "Execute a decision tree mutation or request clarification from user.",
        "input_schema": {
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
                    ],
                    "description": "Action type to execute"
                },
                "payload": {
                    "type": "object",
                    "properties": {
                        "target_parent_id": {"type": "string", "description": "UUID of parent group node"},
                        "target_node_id": {"type": "string", "description": "UUID of target node to replace or remove"},
                        "segment_key": {"type": "string", "description": "Segment key (must exist in known segments catalog)"},
                        "attribute": {"type": "string", "description": "Attribute name"},
                        "operator": {"type": "string", "description": "Allowed operator for attribute type"},
                        "value": {"description": "Filter comparison value"},
                        "group_type": {"type": "string", "enum": ["AND", "OR"]},
                        "question": {"type": "string", "description": "Clarifying question to present to user"},
                        "options": {"type": "array", "items": {"type": "string"}, "description": "Suggested choices"},
                        "reasoning": {"type": "string", "description": "Explanation of action taken"}
                    }
                }
            },
            "required": ["action", "payload"]
        }
    }
]

# 2. OpenAI / OpenRouter Tool Schema
OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "execute_agent_action",
            "description": "Execute a decision tree mutation or request clarification from user.",
            "parameters": ANTHROPIC_TOOLS[0]["input_schema"]
        }
    }
]

class AgentOrchestrator:
    def __init__(self):
        self.open_router_key = settings.open_router_api_key.strip()
        self.openrouter_base_url = settings.openrouter_base_url.rstrip("/").strip()
        self.openrouter_model = settings.openrouter_model.strip()

        self.anthropic_key = settings.anthropic_api_key.strip()
        self.openai_key = settings.openai_api_key.strip()
        self.openai_base_url = settings.openai_base_url.rstrip("/").strip()
        self.openai_model = settings.openai_model.strip()

        self.anthropic_client = (
            anthropic.Anthropic(api_key=self.anthropic_key)
            if self.anthropic_key and self.anthropic_key != "anthropic_placeholder"
            else None
        )

    async def process_user_turn(
        self,
        user_message: str,
        current_tree_dict: Dict[str, Any],
        known_segments: List[str],
        known_attributes: List[Dict[str, Any]],
        conversation_history: List[Dict[str, Any]]
    ) -> List[AgentAction]:

        system_prompt = f"""You are an AI Decision-Tree Agent constructing boolean targeting rules for audience segmentation.

STRICT OPERATIONAL DIRECTIVES:
1. You DO NOT mutate tree state directly. You MUST call the `execute_agent_action` tool to perform any tree modifications.
2. Segment Validation: You may ONLY add segments that exist in the KNOWN SEGMENTS catalog below. If a user asks for an unknown segment or an ambiguous concept (e.g., "recent buyers"), call `REQUEST_CLARIFICATION` to ask the user for clarification or push back with valid alternatives.
3. Attribute Validation: Attribute names and operators MUST match the KNOWN ATTRIBUTES catalog below. Push back on invalid attribute names or invalid operators (e.g. comparing string with > operator).
4. Node Mutation Addressing: When replacing or removing a node, specify `target_node_id` matching a node UUID from the CURRENT DECISION TREE.
5. Value Boundaries: Attribute `account_age_days` MUST NOT exceed 10000 (maximum allowed by validator). If a user specifies years that convert to > 10000 days (e.g., 40 years = 14600 days), cap/clamp `account_age_days` to 10000 max.

KNOWN SEGMENTS CATALOG:
{json.dumps(known_segments)}

KNOWN ATTRIBUTES CATALOG:
{json.dumps(known_attributes, indent=2)}

CURRENT DECISION TREE AST (With UUID Node IDs):
{json.dumps(current_tree_dict, indent=2)}
"""

        # Priority 1: OpenRouter API (Recommended when OPEN_ROUTER_API_KEY is configured)
        if self.open_router_key and self.open_router_key != "openrouter_placeholder":
            print(f"[AgentOrchestrator] Routing LLM request to OpenRouter ({self.openrouter_model})...")
            return await self._call_openrouter(system_prompt, user_message, conversation_history, current_tree_dict, known_segments, known_attributes)

        # Priority 2: Direct Anthropic Claude API
        if self.anthropic_client:
            print("[AgentOrchestrator] Routing LLM request to Anthropic Claude API...")
            return await self._call_anthropic(system_prompt, user_message, conversation_history, current_tree_dict, known_segments, known_attributes)

        # Priority 3: Direct OpenAI / OpenAI-compatible API
        if self.openai_key and self.openai_key != "openai_placeholder":
            print(f"[AgentOrchestrator] Routing LLM request to OpenAI ({self.openai_model})...")
            return await self._call_openai_compatible(system_prompt, user_message, conversation_history, current_tree_dict, known_segments, known_attributes)

        # Priority 4: Deterministic Offline Heuristic Engine Fallback
        print("[AgentOrchestrator] No LLM API keys detected. Using Deterministic Offline Heuristic Engine...")
        return self._heuristic_fallback(user_message, current_tree_dict, known_segments, known_attributes, conversation_history)

    async def _call_openrouter(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: List[Dict[str, Any]],
        current_tree_dict: Dict[str, Any],
        known_segments: List[str],
        known_attributes: List[Dict[str, Any]]
    ) -> List[AgentAction]:
        messages = [{"role": "system", "content": system_prompt}]
        for msg in conversation_history[-6:]:
            role = "user" if msg["sender"] == "user" else "assistant"
            messages.append({"role": role, "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": self.openrouter_model,
            "messages": messages,
            "tools": OPENAI_TOOLS,
            "tool_choice": "auto"
        }

        headers = {
            "Authorization": f"Bearer {self.open_router_key.strip()}",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "AI Decision-Tree Agent",
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                resp = await client.post(f"{self.openrouter_base_url}/chat/completions", json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()

            choice = data["choices"][0]["message"]
            actions = []

            if "tool_calls" in choice and choice["tool_calls"]:
                for tc in choice["tool_calls"]:
                    if tc["function"]["name"] == "execute_agent_action":
                        args = json.loads(tc["function"]["arguments"])
                        payload_data = args.get("payload") if isinstance(args.get("payload"), dict) else {k: v for k, v in args.items() if k != "action"}
                        action_obj = AgentAction(
                            action=ActionType(args["action"]),
                            payload=AgentActionPayload(**payload_data)
                        )
                        actions.append(action_obj)

            if not actions:
                content = choice.get("content") or "Could you clarify your targeting requirement?"
                actions.append(AgentAction(
                    action=ActionType.REQUEST_CLARIFICATION,
                    payload=AgentActionPayload(question=content)
                ))

            return actions

        except Exception as e:
            print(f"[AgentOrchestrator] OpenRouter API error: {e}")
            return self._heuristic_fallback(user_message, current_tree_dict, known_segments, known_attributes, conversation_history)

    async def _call_anthropic(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: List[Dict[str, Any]],
        current_tree_dict: Dict[str, Any],
        known_segments: List[str],
        known_attributes: List[Dict[str, Any]]
    ) -> List[AgentAction]:
        messages_payload = []
        for msg in conversation_history[-6:]:
            role = "user" if msg["sender"] == "user" else "assistant"
            messages_payload.append({"role": role, "content": msg["content"]})
        messages_payload.append({"role": "user", "content": user_message})

        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                system=system_prompt,
                messages=messages_payload,
                tools=ANTHROPIC_TOOLS
            )

            actions = []
            for block in response.content:
                if block.type == "tool_use" and block.name == "execute_agent_action":
                    input_data = block.input
                    payload_data = input_data.get("payload") if isinstance(input_data.get("payload"), dict) else {k: v for k, v in input_data.items() if k != "action"}
                    action_obj = AgentAction(
                        action=ActionType(input_data["action"]),
                        payload=AgentActionPayload(**payload_data)
                    )
                    actions.append(action_obj)

            if not actions:
                text_response = "".join([b.text for b in response.content if hasattr(b, "text")])
                actions.append(AgentAction(
                    action=ActionType.REQUEST_CLARIFICATION,
                    payload=AgentActionPayload(question=text_response or "Could you clarify your targeting requirement?")
                ))
            return actions

        except Exception as e:
            print(f"[AgentOrchestrator] Anthropic API error: {e}")
            return self._heuristic_fallback(user_message, current_tree_dict, known_segments, known_attributes, conversation_history)

    async def _call_openai_compatible(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: List[Dict[str, Any]],
        current_tree_dict: Dict[str, Any],
        known_segments: List[str],
        known_attributes: List[Dict[str, Any]]
    ) -> List[AgentAction]:
        messages = [{"role": "system", "content": system_prompt}]
        for msg in conversation_history[-6:]:
            role = "user" if msg["sender"] == "user" else "assistant"
            messages.append({"role": role, "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": self.openai_model,
            "messages": messages,
            "tools": OPENAI_TOOLS,
            "tool_choice": "auto"
        }

        headers = {
            "Authorization": f"Bearer {self.openai_key.strip()}",
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(f"{self.openai_base_url}/chat/completions", json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()

            choice = data["choices"][0]["message"]
            actions = []

            if "tool_calls" in choice and choice["tool_calls"]:
                for tc in choice["tool_calls"]:
                    if tc["function"]["name"] == "execute_agent_action":
                        args = json.loads(tc["function"]["arguments"])
                        action_obj = AgentAction(
                            action=ActionType(args["action"]),
                            payload=AgentActionPayload(**args["payload"])
                        )
                        actions.append(action_obj)

            if not actions:
                content = choice.get("content") or "Could you clarify your targeting requirement?"
                actions.append(AgentAction(
                    action=ActionType.REQUEST_CLARIFICATION,
                    payload=AgentActionPayload(question=content)
                ))

            return actions

        except Exception as e:
            print(f"[AgentOrchestrator] OpenAI-compatible API error: {e}")
            return self._heuristic_fallback(user_message, current_tree_dict, known_segments, known_attributes, conversation_history)

    def _heuristic_fallback(
        self,
        user_message: str,
        current_tree_dict: Dict[str, Any],
        known_segments: List[str],
        known_attributes: List[Dict[str, Any]],
        conversation_history: List[Dict[str, Any]] = None
    ) -> List[AgentAction]:
        """
        Deterministic heuristic reasoning engine used for offline testing or when no API key is configured.
        """
        msg_lower = user_message.lower().strip()

        # Check if user is confirming a clarification suggestion from previous message
        if msg_lower in ["ok", "yes", "sure", "yep", "correct", "agree", "confirm"] and conversation_history:
            for prev in reversed(conversation_history):
                if prev.get("sender") in ["agent", "assistant"]:
                    prev_text = prev.get("content", "")
                    import re
                    suggested = re.findall(r"['\"]([a-zA-Z0-9_\-]+)['\"]", prev_text)
                    for seg in suggested:
                        if not known_segments or seg in known_segments:
                            return [AgentAction(
                                action=ActionType.ADD_SEGMENT,
                                payload=AgentActionPayload(segment_key=seg, reasoning=f"Confirmed suggested segment '{seg}'")
                            )]
                    break

        matched_segments = [s for s in known_segments if s.lower() in msg_lower or s.replace("_", " ").lower() in msg_lower]

        matched_attrs = []
        for attr in known_attributes:
            aid = attr.get("id", "")
            aname = attr.get("name", "").lower()
            if aid.lower() in msg_lower or aname in msg_lower:
                op = "=="
                val = True
                if ">=" in msg_lower:
                    op = ">="
                elif "<=" in msg_lower:
                    op = "<="
                elif ">" in msg_lower:
                    op = ">"
                elif "<" in msg_lower:
                    op = "<"

                import re
                nums = re.findall(r'\d+', msg_lower)
                if nums:
                    val = int(nums[0])
                matched_attrs.append((aid, op, val))

        actions = []
        for seg in matched_segments:
            actions.append(AgentAction(
                action=ActionType.ADD_SEGMENT,
                payload=AgentActionPayload(segment_key=seg, reasoning=f"Discovered matching segment '{seg}'")
            ))

        for aid, op, val in matched_attrs:
            actions.append(AgentAction(
                action=ActionType.ADD_ATTRIBUTE,
                payload=AgentActionPayload(attribute=aid, operator=op, value=val, reasoning=f"Extracted attribute filter '{aid} {op} {val}'")
            ))

        if not actions:
            if "recent" in msg_lower or "active" in msg_lower:
                actions.append(AgentAction(
                    action=ActionType.REQUEST_CLARIFICATION,
                    payload=AgentActionPayload(
                        question="By recent users, how many days back should we filter, or which specific segment key do you mean?",
                        options=[s for s in known_segments if "active" in s or "recent" in s] or ["recently_active", "active_30d"]
                    )
                ))
            else:
                sample_segs = known_segments[:5] if known_segments else ["high_value_customers", "recently_active"]
                actions.append(AgentAction(
                    action=ActionType.REQUEST_CLARIFICATION,
                    payload=AgentActionPayload(
                        question=f"I couldn't match your request to known segments or attributes. Available segments: {', '.join(sample_segs)}...",
                        options=known_segments[:4] if known_segments else ["high_value_customers", "recently_active"]
                    )
                ))

        return actions
