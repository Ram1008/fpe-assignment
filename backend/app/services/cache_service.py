import asyncio
import datetime
from typing import Dict, Any, List, Optional
from app.config import settings
from app.services.persistence_service import PersistenceService
from app.services.external.users_client import UsersClient
from app.services.external.attributes_client import AttributesClient

class CacheService:
    def __init__(self, persistence: PersistenceService):
        self.persistence = persistence
        self.users_client = UsersClient()
        self.attributes_client = AttributesClient()
        self._is_bootstrapping = False
        self._last_error: Optional[str] = None

    async def get_status(self) -> Dict[str, Any]:
        segments_item = await self.persistence.get_cache_item("discovered_segments")
        attributes_item = await self.persistence.get_cache_item("attribute_schema")
        
        has_valid_segments = self._is_ttl_valid(segments_item)
        has_valid_attributes = self._is_ttl_valid(attributes_item)

        if self._is_bootstrapping:
            status = "BOOTSTRAPPING"
        elif has_valid_segments and has_valid_attributes:
            status = "READY"
        elif segments_item or attributes_item:
            status = "EXPIRED"
        else:
            status = "UNINITIALIZED"

        return {
            "status": status,
            "is_bootstrapping": self._is_bootstrapping,
            "segments_count": len(segments_item["data"]) if segments_item else 0,
            "segments_cache_timestamp": segments_item["fetched_at"] if segments_item else None,
            "attributes_count": len(attributes_item["data"]) if attributes_item else 0,
            "last_error": self._last_error
        }

    def _is_ttl_valid(self, cache_item: Optional[Dict[str, Any]]) -> bool:
        if not cache_item:
            return False
        fetched_at_str = cache_item.get("fetched_at")
        if not fetched_at_str:
            return False
        try:
            fetched_at = datetime.datetime.fromisoformat(fetched_at_str)
            if fetched_at.tzinfo is None:
                fetched_at = fetched_at.replace(tzinfo=datetime.timezone.utc)
            now = datetime.datetime.now(datetime.timezone.utc)
            ttl = cache_item.get("ttl_seconds", settings.ttl_seconds)
            return (now - fetched_at).total_seconds() < ttl
        except Exception:
            return False

    async def get_segments(self) -> List[str]:
        item = await self.persistence.get_cache_item("discovered_segments")
        if item and "data" in item:
            return item["data"]
        return []

    async def get_segments_cache_timestamp(self) -> str:
        item = await self.persistence.get_cache_item("discovered_segments")
        if item and "fetched_at" in item:
            return item["fetched_at"]
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    async def get_attributes(self) -> List[Dict[str, Any]]:
        item = await self.persistence.get_cache_item("attribute_schema")
        if item and "data" in item:
            return item["data"]
        return []

    async def ensure_cache(self) -> None:
        """
        Hybrid async bootstrap entry point.
        Checks if cache is valid. If invalid or missing, launches async discovery task.
        """
        segments_item = await self.persistence.get_cache_item("discovered_segments")
        attributes_item = await self.persistence.get_cache_item("attribute_schema")

        if self._is_ttl_valid(segments_item) and self._is_ttl_valid(attributes_item):
            print("[CacheService] Valid 24h cache found. Zero Users API calls required.")
            return

        if not self._is_bootstrapping:
            asyncio.create_task(self.refresh_cache_background())

    async def refresh_cache_background(self) -> None:
        if self._is_bootstrapping:
            return
        self._is_bootstrapping = True
        self._last_error = None
        print("[CacheService] Starting background cache refresh...")

        try:
            # 1. Attributes Discovery
            attrs = await self.attributes_client.list_attributes()
            await self.persistence.set_cache_item("attribute_schema", attrs, ttl_seconds=settings.ttl_seconds)
            print(f"[CacheService] Cached {len(attrs)} user attributes.")

            # 2. Segments Discovery (Check if incremental sync is possible)
            segments_item = await self.persistence.get_cache_item("discovered_segments")
            if segments_item and segments_item.get("fetched_at"):
                # Incremental sync via /v1/users/changes
                last_sync = segments_item["fetched_at"]
                print(f"[CacheService] Attempting incremental segment sync since {last_sync}...")
                try:
                    changes_data = await self.users_client.get_users_changes(since=last_sync)
                    changed_items = changes_data.get("items", [])
                    new_segments = set(segments_item.get("data", []))
                    for user in changed_items:
                        new_segments.update(user.get("segments", []))
                    sorted_segs = sorted(list(new_segments))
                    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    await self.persistence.set_cache_item("discovered_segments", sorted_segs, ttl_seconds=settings.ttl_seconds)
                    print(f"[CacheService] Incremental sync complete. Total segments: {len(sorted_segs)}")
                except Exception as inc_err:
                    print(f"[CacheService] Incremental sync failed ({inc_err}), falling back to full discovery.")
                    segments, timestamp = await self.users_client.discover_all_segments()
                    await self.persistence.set_cache_item("discovered_segments", segments, ttl_seconds=settings.ttl_seconds)
            else:
                # Full discovery
                print("[CacheService] Performing full user segment discovery...")
                segments, timestamp = await self.users_client.discover_all_segments()
                await self.persistence.set_cache_item("discovered_segments", segments, ttl_seconds=settings.ttl_seconds)
                print(f"[CacheService] Full discovery complete. Discovered {len(segments)} unique segments.")
        except Exception as e:
            self._last_error = str(e)
            print(f"[CacheService] Cache discovery error: {e}")
        finally:
            self._is_bootstrapping = False
