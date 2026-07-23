import httpx
from typing import Dict, Any, List, Optional, Tuple
from app.config import settings

class UsersClient:
    def __init__(self, base_url: str = settings.base_api_url, bearer_token: str = settings.bearer_token):
        self.base_url = base_url.rstrip("/")
        self.bearer_token = bearer_token

    def _headers(self, etag: Optional[str] = None) -> Dict[str, str]:
        h = {"Accept": "application/json"}
        if self.bearer_token:
            h["Authorization"] = f"Bearer {self.bearer_token}"
        if etag:
            h["If-None-Match"] = etag
        return h

    async def get_meta(self) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{self.base_url}/v1/users/meta",
                headers=self._headers()
            )
            resp.raise_for_status()
            return resp.json()

    async def get_users_page(self, limit: int = 1000, offset: int = 0, etag: Optional[str] = None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{self.base_url}/v1/users",
                params={"limit": limit, "offset": offset},
                headers=self._headers(etag)
            )
            if resp.status_code == 304:
                return None, etag
            resp.raise_for_status()
            new_etag = resp.headers.get("ETag")
            return resp.json(), new_etag

    async def get_users_changes(self, since: str, limit: int = 1000, offset: int = 0) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{self.base_url}/v1/users/changes",
                params={"since": since, "limit": limit, "offset": offset},
                headers=self._headers()
            )
            resp.raise_for_status()
            return resp.json()

    async def discover_all_segments(self) -> Tuple[List[str], str]:
        """
        Iterates over paginated /v1/users to collect all unique segment keys.
        Returns a tuple of (unique_segments_list, timestamp).
        """
        import datetime
        segments_set = set()
        offset = 0
        limit = 1000
        has_more = True
        sync_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        try:
            while has_more:
                page_data, _ = await self.get_users_page(limit=limit, offset=offset)
                if not page_data:
                    break
                items = page_data.get("items", [])
                for user in items:
                    user_segments = user.get("segments", [])
                    segments_set.update(user_segments)
                
                has_more = page_data.get("has_more", False)
                offset += len(items)
                if not items:
                    break
        except Exception as e:
            print(f"[UsersClient] Warning during segment discovery: {e}")

        return sorted(list(segments_set)), sync_timestamp
