import os
import sys
from pydantic_settings import BaseSettings

# Ensure backend root is in sys.path
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

_root_dir = os.path.dirname(_backend_dir)
_env_path = os.path.join(_root_dir, ".env") if os.path.exists(os.path.join(_root_dir, ".env")) else ".env"

class Settings(BaseSettings):
    bearer_token: str = os.getenv("BEARER_TOKEN", "").strip()
    open_router_api_key: str = os.getenv("OPEN_ROUTER_API_KEY", "").strip()
    openrouter_base_url: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").strip()
    openrouter_model: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini").strip()
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "").strip()
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "").strip()
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
    base_api_url: str = os.getenv("BASE_API_URL", "https://dt-agent-support.divyanshgolyan.workers.dev")
    database_path: str = os.getenv("DATABASE_PATH", "app_data.db")
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))
    frontend_port: int = int(os.getenv("FRONTEND_PORT", "3000"))
    ttl_seconds: int = 86400  # 24 hours

    class Config:
        env_file = _env_path
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
