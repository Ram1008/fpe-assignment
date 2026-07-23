from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from app.services.persistence_service import PersistenceService
from app.services.cache_service import CacheService
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/api/conversations", tags=["Conversations"])

class CreateConversationRequest(BaseModel):
    title: Optional[str] = "New Audience Targeting Tree"

class UserMessageRequest(BaseModel):
    content: str

def get_services():
    persistence = PersistenceService()
    cache = CacheService(persistence)
    conv_service = ConversationService(persistence, cache)
    return persistence, cache, conv_service

@router.post("")
async def create_conversation(req: CreateConversationRequest):
    persistence, cache, _ = get_services()
    conv_id = await persistence.create_conversation(title=req.title or "New Audience Targeting Tree")
    # Initialize empty tree snapshot
    from app.domain.tree_engine import TreeEngine
    engine = TreeEngine()
    await persistence.save_tree_snapshot(conv_id, engine.to_dict(), is_valid=False)
    return {"conversation_id": conv_id, "title": req.title, "tree": engine.to_dict()}

@router.get("")
async def list_conversations():
    persistence, _, _ = get_services()
    return await persistence.list_conversations()

@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str):
    persistence, _, _ = get_services()
    messages = await persistence.get_messages(conversation_id)
    snapshot = await persistence.get_latest_tree_snapshot(conversation_id)
    return {
        "conversation_id": conversation_id,
        "messages": messages,
        "tree_snapshot": snapshot
    }

@router.post("/{conversation_id}/messages")
async def send_message(conversation_id: str, req: UserMessageRequest):
    _, cache, conv_service = get_services()
    await cache.ensure_cache()
    if not req.content.strip():
        raise HTTPException(status_code=400, detail="Message content cannot be empty")
    return await conv_service.execute_turn(conversation_id, req.content)
