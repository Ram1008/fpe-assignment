import os
import json
import uuid
import datetime
import aiosqlite
from typing import Dict, Any, List, Optional
from app.config import settings

class PersistenceService:
    def __init__(self, db_path: str = settings.database_path):
        self.db_path = db_path

    async def init_db(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    content TEXT NOT NULL,
                    action_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                );
            """)
            await db.execute("""
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
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS metadata_cache (
                    cache_key TEXT PRIMARY KEY,
                    data_json TEXT NOT NULL,
                    fetched_at TIMESTAMP NOT NULL,
                    etag TEXT,
                    ttl_seconds INTEGER DEFAULT 86400
                );
            """)
            await db.commit()

    async def create_conversation(self, title: str = "New Audience Targeting Tree") -> str:
        conv_id = f"conv_{uuid.uuid4().hex[:8]}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (conv_id, title, now, now)
            )
            await db.commit()
        return conv_id

    async def list_conversations(self) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC") as cursor:
                rows = await cursor.fetchall()
                return [{"id": r[0], "title": r[1], "created_at": r[2], "updated_at": r[3]} for r in rows]

    async def add_message(self, conversation_id: str, sender: str, content: str, action_json: Optional[str] = None) -> str:
        msg_id = f"msg_{uuid.uuid4().hex[:8]}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO messages (id, conversation_id, sender, content, action_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (msg_id, conversation_id, sender, content, action_json, now)
            )
            await db.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (now, conversation_id)
            )
            await db.commit()
        return msg_id

    async def get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT id, sender, content, action_json, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
                (conversation_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        "id": r[0],
                        "sender": r[1],
                        "content": r[2],
                        "action_json": json.loads(r[3]) if r[3] else None,
                        "created_at": r[4]
                    }
                    for r in rows
                ]

    async def save_tree_snapshot(self, conversation_id: str, tree_dict: Dict[str, Any], is_valid: bool = False, validation_report: Optional[Dict[str, Any]] = None) -> str:
        snap_id = f"snap_{uuid.uuid4().hex[:8]}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        tree_json = json.dumps(tree_dict)
        report_json = json.dumps(validation_report) if validation_report else None

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM tree_snapshots WHERE conversation_id = ?", (conversation_id,)) as cursor:
                count_row = await cursor.fetchone()
                version = (count_row[0] if count_row else 0) + 1

            await db.execute(
                "INSERT INTO tree_snapshots (id, conversation_id, version, tree_json, is_valid, validation_report, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (snap_id, conversation_id, version, tree_json, is_valid, report_json, now)
            )
            await db.commit()
        return snap_id

    async def get_latest_tree_snapshot(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT tree_json, is_valid, validation_report FROM tree_snapshots WHERE conversation_id = ? ORDER BY version DESC LIMIT 1",
                (conversation_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        "tree": json.loads(row[0]),
                        "is_valid": bool(row[1]),
                        "validation_report": json.loads(row[2]) if row[2] else None
                    }
        return None

    # Cache table helpers
    async def get_cache_item(self, key: str) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT data_json, fetched_at, etag, ttl_seconds FROM metadata_cache WHERE cache_key = ?", (key,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        "data": json.loads(row[0]),
                        "fetched_at": row[1],
                        "etag": row[2],
                        "ttl_seconds": row[3]
                    }
        return None

    async def set_cache_item(self, key: str, data: Any, etag: Optional[str] = None, ttl_seconds: int = 86400) -> None:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        data_json = json.dumps(data)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO metadata_cache (cache_key, data_json, fetched_at, etag, ttl_seconds) VALUES (?, ?, ?, ?, ?) ON CONFLICT(cache_key) DO UPDATE SET data_json=excluded.data_json, fetched_at=excluded.fetched_at, etag=excluded.etag, ttl_seconds=excluded.ttl_seconds",
                (key, data_json, now, etag, ttl_seconds)
            )
            await db.commit()
