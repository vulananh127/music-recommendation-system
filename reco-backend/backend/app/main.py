from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from bd import get_pool
from es import get_client
from cache import RedisCache
from routers import recommend, events, health, auth, playlists, search, playlist_tracks, public

app = FastAPI(
    title="Music Recommendation Backend",
    description="Backend API cho hệ thống gợi ý nhạc - Optimized",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong production nên giới hạn
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    """
    Khởi tạo resources khi app start
    """
    print("[STARTUP] Initializing database pool...")
    app.state.db = await get_pool()
    
    print("[STARTUP] Initializing Elasticsearch client...")
    app.state.es = get_client()
    
    print("[STARTUP] Initializing Redis cache...")
    app.state.cache = RedisCache()
    
    print("[STARTUP] All services initialized successfully!")

@app.on_event("shutdown")
async def shutdown():
    """
    Cleanup resources khi app shutdown
    """
    print("[SHUTDOWN] Closing database pool...")
    await app.state.db.close()
    
    print("[SHUTDOWN] Closing Elasticsearch client...")
    await app.state.es.aclose()
    
    print("[SHUTDOWN] Closing Redis cache...")
    await app.state.cache.close()
    
    print("[SHUTDOWN] Cleanup completed!")

# Dependency injection middleware
@app.middleware("http")
async def inject_state(request: Request, call_next):
    """
    Inject dependencies vào request state
    """
    request.state.db = app.state.db
    request.state.es = app.state.es
    request.state.cache = app.state.cache
    response = await call_next(request)
    return response

# Route registration
app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix="/api", tags=["authentication"])
app.include_router(playlists.router, prefix="/api", tags=["playlists"])
app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(playlist_tracks.router, prefix="/api", tags=["playlist-tracks"])
app.include_router(recommend.router, prefix="/api", tags=["recommend"])
app.include_router(events.router, prefix="/api", tags=["events"])
app.include_router(public.router, prefix="/api", tags=["public"])

# Performance monitoring endpoint
@app.get("/metrics")
async def get_metrics():
    """
    Endpoint để monitor health của các services
    """
    try:
        # Check DB
        async with app.state.db.acquire() as conn:
            db_status = await conn.fetchval("SELECT 1")
        db_healthy = db_status == 1
    except:
        db_healthy = False
    
    try:
        # Check ES
        es_response = await app.state.es.get("/_cluster/health")
        es_healthy = es_response.status_code == 200
    except:
        es_healthy = False
    
    try:
        # Check Redis
        redis_healthy = await app.state.cache.exists("health_check")
        await app.state.cache.set("health_check", "ok", ttl=60)
    except:
        redis_healthy = False
    
    return {
        "database": {"healthy": db_healthy},
        "elasticsearch": {"healthy": es_healthy},
        "cache": {"healthy": redis_healthy},
        "overall": db_healthy and es_healthy and redis_healthy
    }