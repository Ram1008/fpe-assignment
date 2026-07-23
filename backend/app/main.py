import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.services.persistence_service import PersistenceService
from app.services.cache_service import CacheService
from app.api import conversations, validation, cache

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize SQLite tables and trigger hybrid async cache check
    print("[FastAPI Server Startup] Initializing persistence & cache services...")
    persistence = PersistenceService()
    await persistence.init_db()
    
    cache_service = CacheService(persistence)
    await cache_service.ensure_cache()
    yield
    # Shutdown
    print("[FastAPI Server Shutdown] Cleaning up server resources...")

app = FastAPI(
    title="AI Decision-Tree Agent Backend",
    version="1.0.0",
    description="Backend API for AI Decision-Tree Agent",
    lifespan=lifespan
)

# Enable CORS for localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(conversations.router)
app.include_router(validation.router)
app.include_router(cache.router)

@app.get("/")
async def root():
    return {
        "app": "AI Decision-Tree Agent",
        "status": "online",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.backend_port, reload=True)
