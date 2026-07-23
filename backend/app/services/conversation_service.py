import json
import time
from typing import Dict, Any, List, Optional
from app.domain.tree_engine import TreeEngine
from app.domain.models import AgentAction, ActionType
from app.services.persistence_service import PersistenceService
from app.services.cache_service import CacheService
from app.services.agent_orchestrator import AgentOrchestrator
from app.services.external.validator_client import ValidatorClient
from app.observability.logger import log_event

class ConversationService:
    def __init__(self, persistence: PersistenceService, cache: CacheService):
        self.persistence = persistence
        self.cache = cache
        self.orchestrator = AgentOrchestrator()
        self.validator_client = ValidatorClient()

    async def execute_turn(self, conversation_id: str, user_message_text: str) -> Dict[str, Any]:
        start_time = time.time()

        # 1. Load latest tree snapshot or initialize new tree
        snapshot = await self.persistence.get_latest_tree_snapshot(conversation_id)
        if snapshot and snapshot.get("tree"):
            tree_engine = TreeEngine.from_dict(snapshot["tree"])
        else:
            tree_engine = TreeEngine()

        # 2. Record user message
        await self.persistence.add_message(conversation_id, sender="user", content=user_message_text)

        # 3. Fetch cache metadata for prompt context
        known_segments = await self.cache.get_segments()
        known_attributes = await self.cache.get_attributes()
        history = await self.persistence.get_messages(conversation_id)

        # 4. Invoke LLM reasoning
        actions: List[AgentAction] = await self.orchestrator.process_user_turn(
            user_message=user_message_text,
            current_tree_dict=tree_engine.to_dict(),
            known_segments=known_segments,
            known_attributes=known_attributes,
            conversation_history=history
        )

        agent_response_lines = []
        applied_actions = []
        pending_clarification = None

        # 5. Apply Agent Actions to Tree Engine
        for action in actions:
            act_type = action.action
            payload = action.payload

            if act_type == ActionType.ADD_SEGMENT and payload.segment_key:
                if payload.segment_key in known_segments:
                    tree_engine.add_segment(payload.segment_key, parent_id=payload.target_parent_id)
                    agent_response_lines.append(f"Added segment '{payload.segment_key}'.")
                    applied_actions.append(action.model_dump())
                else:
                    agent_response_lines.append(f"Segment '{payload.segment_key}' is unknown. Proposed alternatives: {', '.join(known_segments[:3])}.")

            elif act_type == ActionType.ADD_ATTRIBUTE and payload.attribute:
                tree_engine.add_attribute(
                    attribute=payload.attribute,
                    operator=payload.operator or "==",
                    value=payload.value,
                    parent_id=payload.target_parent_id
                )
                agent_response_lines.append(f"Added attribute filter '{payload.attribute} {payload.operator or '=='} {payload.value}'.")
                applied_actions.append(action.model_dump())

            elif act_type == ActionType.REMOVE_NODE and payload.target_node_id:
                success = tree_engine.remove_node(payload.target_node_id)
                if success:
                    agent_response_lines.append(f"Removed node '{payload.target_node_id}'.")
                    applied_actions.append(action.model_dump())

            elif act_type == ActionType.ADD_BOOLEAN_GROUP and payload.group_type:
                new_grp = tree_engine.add_boolean_group(payload.group_type, parent_id=payload.target_parent_id)
                agent_response_lines.append(f"Added boolean group '{payload.group_type}'.")
                applied_actions.append(action.model_dump())

            elif act_type == ActionType.REQUEST_CLARIFICATION:
                pending_clarification = {
                    "question": payload.question or "Please clarify your targeting criteria.",
                    "options": payload.options or []
                }
                agent_response_lines.append(payload.question or "Please clarify.")
                applied_actions.append(action.model_dump())

        if not agent_response_lines:
            agent_response_lines.append("I have evaluated your request.")

        agent_text = "\n".join(agent_response_lines)

        # 6. Validate tree state against Validator API
        cache_ts = await self.cache.get_segments_cache_timestamp()
        validator_payload = tree_engine.serialize_for_validator()
        validation_report = await self.validator_client.validate_tree(validator_payload, cache_ts)
        is_valid = validation_report.get("ok", False)

        # 7. Persist tree snapshot and agent message
        await self.persistence.save_tree_snapshot(conversation_id, tree_engine.to_dict(), is_valid=is_valid, validation_report=validation_report)
        msg_id = await self.persistence.add_message(conversation_id, sender="agent", content=agent_text, action_json=json.dumps(applied_actions))

        elapsed_ms = int((time.time() - start_time) * 1000)
        log_event(
            event_type="agent_turn_executed",
            payload={"conversation_id": conversation_id, "actions_count": len(applied_actions), "is_valid": is_valid},
            latency_ms=elapsed_ms,
            cache_hit=True
        )

        return {
            "message_id": msg_id,
            "agent_response": agent_text,
            "actions_taken": applied_actions,
            "tree": tree_engine.to_dict(),
            "validator_payload": validator_payload,
            "validation_report": validation_report,
            "pending_clarification": pending_clarification
        }
