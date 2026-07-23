import httpx
from typing import Dict, Any
from app.config import settings

class ValidatorClient:
    def __init__(self, base_url: str = settings.base_api_url, bearer_token: str = settings.bearer_token):
        self.base_url = base_url.rstrip("/")
        self.bearer_token = bearer_token

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.bearer_token:
            h["Authorization"] = f"Bearer {self.bearer_token}"
        return h

    async def validate_tree(self, tree_payload: Dict[str, Any], segments_cache_timestamp: str) -> Dict[str, Any]:
        """
        POST to /v1/validate with tree payload and segments_cache_timestamp.
        """
        request_body = {
            "tree": tree_payload,
            "segments_cache_timestamp": segments_cache_timestamp
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.base_url}/v1/validate",
                    json=request_body,
                    headers=self._headers()
                )
                if resp.status_code == 400:
                    return {
                        "ok": False,
                        "errors": [{"path": "#", "code": "INVALID_FORMAT", "message": resp.text}],
                        "warnings": []
                    }
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            return {
                "ok": False,
                "errors": [{"path": "#", "code": "VALIDATOR_CONNECTION_ERROR", "message": str(e)}],
                "warnings": []
            }
