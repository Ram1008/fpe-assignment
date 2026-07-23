from fastapi import APIRouter
from app.services.persistence_service import PersistenceService
from app.services.cache_service import CacheService

router = APIRouter(prefix="/api/cache", tags=["Cache & Metadata"])

@router.get("/status")
async def get_cache_status():
    persistence = PersistenceService()
    cache = CacheService(persistence)
    return await cache.get_status()

@router.post("/refresh")
async def trigger_cache_refresh():
    persistence = PersistenceService()
    cache = CacheService(persistence)
    await cache.refresh_cache_background()
    return {"message": "Background cache refresh initiated."}
