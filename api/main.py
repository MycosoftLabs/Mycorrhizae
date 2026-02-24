"""
Mycorrhizae Protocol FastAPI Application

Main API server for the Mycorrhizae Protocol.
"""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

import asyncpg
from fastapi import FastAPI, HTTPException, Request, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings

from mycorrhizae import MycorrhizaeProtocol
from services.key_service import KeyServiceManager, KeyService


class Settings(BaseSettings):
    """Application settings from environment."""
    # Use env vars in real deployments; these defaults are placeholders only.
    database_url: str = "postgresql://mindex:change-me@192.168.0.189:5432/mindex"
    redis_url: str = "redis://192.168.0.189:6379"

    # One-time bootstrap token used to mint the FIRST admin API key.
    # Required for POST /api/keys/bootstrap.
    bootstrap_token: Optional[str] = None
    
    # CORS
    cors_origins: str = "*"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8002
    
    class Config:
        env_prefix = "MYCORRHIZAE_"


settings = Settings()

# Global instances
db_pool: Optional[asyncpg.Pool] = None
key_service: Optional[KeyServiceManager] = None
protocol: Optional[MycorrhizaeProtocol] = None
redis_broker = None


async def get_db_pool() -> asyncpg.Pool:
    """Get database connection pool."""
    global db_pool
    if db_pool is None:
        raise HTTPException(status_code=503, detail="Database not available")
    return db_pool


async def get_key_service() -> KeyServiceManager:
    """Get key service instance."""
    global key_service
    if key_service is None:
        raise HTTPException(status_code=503, detail="Key service not available")
    return key_service


async def get_protocol() -> MycorrhizaeProtocol:
    """Get protocol instance."""
    global protocol
    if protocol is None:
        raise HTTPException(status_code=503, detail="Protocol not available")
    return protocol


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global db_pool, key_service, protocol, redis_broker
    
    # Startup
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting Mycorrhizae Protocol API...")
    
    try:
        # Connect to database
        db_pool = await asyncpg.create_pool(settings.database_url, min_size=2, max_size=10)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Connected to database")
        
        # Initialize key service
        key_service = KeyServiceManager(db_pool=db_pool)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Key service initialized")
        
        # Initialize protocol
        from mycorrhizae.broker import RedisBroker
        redis_broker = RedisBroker(redis_url=settings.redis_url)
        await redis_broker.connect()

        protocol = MycorrhizaeProtocol(key_service=key_service, redis_client=redis_broker)
        await protocol.start()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Protocol started")
        
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Startup error: {e}")
    
    yield
    
    # Shutdown
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Shutting down...")
    
    if protocol:
        await protocol.stop()

    if redis_broker:
        await redis_broker.disconnect()
    
    if db_pool:
        await db_pool.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Mycorrhizae Protocol API",
        description="Data Protocol for Nature - Routing biological sensor data",
        version="1.0.0",
        lifespan=lifespan,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    from api.keys_router import router as keys_router
    from api.channels_router import router as channels_router
    from api.stream_router import router as stream_router
    from api.websocket_router import router as websocket_router
    
    app.include_router(keys_router, prefix="/api/keys", tags=["API Keys"])
    app.include_router(channels_router, prefix="/api/channels", tags=["Channels"])
    app.include_router(stream_router, prefix="/api/stream", tags=["Streaming"])
    app.include_router(websocket_router, prefix="/api/ws", tags=["WebSocket"])
    
    return app


app = create_app()


# ==================== Health & Info Endpoints ====================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    db_ok = db_pool is not None
    protocol_ok = protocol is not None and protocol._started
    
    return {
        "status": "healthy" if db_ok and protocol_ok else "degraded",
        "database": db_ok,
        "protocol": protocol_ok,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/info")
async def get_info(proto: MycorrhizaeProtocol = Depends(get_protocol)):
    """Get API and protocol information."""
    return {
        "name": "Mycorrhizae Protocol",
        "version": proto.VERSION,
        "stats": proto.get_stats(),
    }


@app.get("/api/stats")
async def get_stats(proto: MycorrhizaeProtocol = Depends(get_protocol)):
    """Get protocol statistics."""
    return proto.get_stats()


# ==================== Run Server ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
