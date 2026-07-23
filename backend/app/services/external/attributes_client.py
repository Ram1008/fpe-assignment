import httpx
from typing import Dict, Any, List, Optional
from app.config import settings

class AttributesClient:
    def __init__(self, base_url: str = settings.base_api_url, bearer_token: str = settings.bearer_token):
        self.base_url = base_url.rstrip("/")
        self.bearer_token = bearer_token

    def _headers(self) -> Dict[str, str]:
        h = {"Accept": "application/json"}
        if self.bearer_token:
            h["Authorization"] = f"Bearer {self.bearer_token}"
        return h

    async def list_attributes(self) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{self.base_url}/v1/attributes",
                headers=self._headers()
            )
            resp.raise_for_status()
            return resp.json()

    async def get_attribute_by_id(self, attribute_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{self.base_url}/v1/attributes/{attribute_id}",
                headers=self._headers()
            )
            resp.raise_for_status()
            return resp.json()
