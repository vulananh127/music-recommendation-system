from fastapi import APIRouter, Query, Depends, BackgroundTasks
from typing import List, Optional
import time
from routers.auth import get_current_user, get_current_user_optional
from dependencies import get_db, get_es
from logging_utils import ESLogger
from cache import get_cache, CacheStrategy, generate_cache_key

router = APIRouter()

@router.get("/search/tracks")
async def search_tracks(
    background_tasks: BackgroundTasks,
    query: str = Query(..., min_length=1, description="Search query"),
    artist_filter: Optional[str] = Query(None, description="Filter by artist URI"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db = Depends(get_db),
    es = Depends(get_es)
):
    t0 = time.time()
    
    # Thử cache
    cache = get_cache()
    cache_key = f"search:tracks:{generate_cache_key(query, artist_filter, limit, offset)}"
    
    cached_result = await cache.get(cache_key)
    if cached_result:
        latency = int((time.time() - t0) * 1000)
        cached_result["latency_ms"] = latency
        cached_result["from_cache"] = True
        
        # Only log if user is authenticated
        if current_user:
            logger = ESLogger(es, background_tasks)
            logger.log_event(
                event_type="search",
                user_id=current_user["id"],
                query=query,
                cache_hit=True,
                latency_ms=latency
            )
        
        return cached_result
    
    # Chuẩn bị full-text search query
    # Chuyển query thành tsquery format
    search_query = ' & '.join(query.split())
    
    async with db.acquire() as conn:
        if artist_filter:
            # Tìm kiếm với filter artist
            rows = await conn.fetch("""
                SELECT 
                    t.id, t.track_uri, t.track_name, t.duration_ms,
                    a.artist_name, a.artist_uri,
                    al.album_name, al.album_uri,
                    ts_rank(t.search_vector, to_tsquery('english', $1)) as rank
                FROM tracks t
                INNER JOIN artists a ON t.artist_id = a.id
                LEFT JOIN albums al ON t.album_id = al.id
                WHERE t.search_vector @@ to_tsquery('english', $1)
                    AND a.artist_uri = $2
                ORDER BY rank DESC, t.track_name
                LIMIT $3 OFFSET $4
            """, search_query, artist_filter, limit, offset)
            
            total_count = await conn.fetchval("""
                SELECT COUNT(*)
                FROM tracks t
                INNER JOIN artists a ON t.artist_id = a.id
                WHERE t.search_vector @@ to_tsquery('english', $1)
                    AND a.artist_uri = $2
            """, search_query, artist_filter)
        else:
            # Tìm kiếm không filter
            rows = await conn.fetch("""
                SELECT 
                    t.id, t.track_uri, t.track_name, t.duration_ms,
                    a.artist_name, a.artist_uri,
                    al.album_name, al.album_uri,
                    ts_rank(t.search_vector, to_tsquery('english', $1)) as rank
                FROM tracks t
                INNER JOIN artists a ON t.artist_id = a.id
                LEFT JOIN albums al ON t.album_id = al.id
                WHERE t.search_vector @@ to_tsquery('english', $1)
                ORDER BY rank DESC, t.track_name
                LIMIT $2 OFFSET $3
            """, search_query, limit, offset)
            
            total_count = await conn.fetchval("""
                SELECT COUNT(*)
                FROM tracks t
                WHERE t.search_vector @@ to_tsquery('english', $1)
            """, search_query)
    
    # Helper function to clean whitespace from strings
    def clean_text(text):
        if not text:
            return text
        # Replace newlines and multiple spaces with single space
        return ' '.join(text.split())
    
    tracks = [
        {
            "id": r["id"],
            "track_uri": r["track_uri"],
            "track_name": clean_text(r["track_name"]),
            "artist_name": clean_text(r["artist_name"]),
            "artist_uri": r["artist_uri"],
            "album_name": clean_text(r["album_name"]),
            "album_uri": r["album_uri"],
            "duration_ms": r["duration_ms"],
            "relevance_score": float(r["rank"])
        }
        for r in rows
    ]
    
    latency = int((time.time() - t0) * 1000)
    
    result = {
        "query": query,
        "artist_filter": artist_filter,
        "total_count": total_count,
        "result_count": len(tracks),
        "limit": limit,
        "offset": offset,
        "tracks": tracks,
        "latency_ms": latency,
        "from_cache": False
    }
    
    # Cache kết quả
    await cache.set(cache_key, result, ttl=CacheStrategy.SEARCH_RESULTS)
    
    # Background logging - only if authenticated
    if current_user:
        logger = ESLogger(es, background_tasks)
        logger.log_event(
            event_type="search",
            user_id=current_user["id"],
            query=query,
            artist_filter=artist_filter,
            result_count=len(tracks),
            total_count=total_count,
            cache_hit=False,
            latency_ms=latency
        )
    
    return result


@router.get("/search/artists")
async def search_artists(
    background_tasks: BackgroundTasks,
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db = Depends(get_db),
    es = Depends(get_es)
):
    """
    Tìm kiếm artists sử dụng Full-Text Search - CHỈ artists có trong rules
    """
    t0 = time.time()
    
    # Cache
    cache = get_cache()
    cache_key = f"search:artists:{generate_cache_key(query, limit, offset)}"
    
    cached_result = await cache.get(cache_key)
    if cached_result:
        latency = int((time.time() - t0) * 1000)
        cached_result["latency_ms"] = latency
        cached_result["from_cache"] = True
        
        # Only log if authenticated
        if current_user:
            logger = ESLogger(es, background_tasks)
            logger.log_event(
                event_type="search",
                user_id=current_user["id"],
                query=query,
                cache_hit=True,
                latency_ms=latency
            )
        
        return cached_result
    
    search_query = ' & '.join(query.split())
    
    async with db.acquire() as conn:
        # Query artists
        rows = await conn.fetch("""
            SELECT 
                a.id, a.artist_uri, a.artist_name,
                ts_rank(a.search_vector, to_tsquery('english', $1)) as rank,
                COUNT(DISTINCT t.id) as track_count
            FROM artists a
            LEFT JOIN tracks t ON a.id = t.artist_id
            WHERE a.search_vector @@ to_tsquery('english', $1)
            GROUP BY a.id, a.artist_uri, a.artist_name, a.search_vector
            ORDER BY rank DESC, a.artist_name
            LIMIT $2 OFFSET $3
        """, search_query, limit, offset)
        
        # Count
        total_count = await conn.fetchval("""
            SELECT COUNT(DISTINCT a.id)
            FROM artists a
            WHERE a.search_vector @@ to_tsquery('english', $1)
        """, search_query)
    
    artists = [
        {
            "id": r["id"],
            "artist_uri": r["artist_uri"],
            "artist_name": r["artist_name"],
            "track_count": r["track_count"],
            "relevance_score": float(r["rank"])
        }
        for r in rows
    ]
    
    latency = int((time.time() - t0) * 1000)
    
    result = {
        "query": query,
        "total_count": total_count,
        "result_count": len(artists),
        "limit": limit,
        "offset": offset,
        "artists": artists,
        "latency_ms": latency,
        "from_cache": False
    }
    
    await cache.set(cache_key, result, ttl=CacheStrategy.SEARCH_RESULTS)
    
    # Background logging - only if authenticated
    if current_user:
        logger = ESLogger(es, background_tasks)
        logger.log_event(
            event_type="search",
            user_id=current_user["id"],
            query=query,
            result_count=len(artists),
            total_count=total_count,
            cache_hit=False,
            latency_ms=latency
        )
    
    return result

@router.get("/search/playlists")
async def search_playlists(
    background_tasks: BackgroundTasks,
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    es = Depends(get_es)
):
    """
    Tìm kiếm playlists của user sử dụng Full-Text Search
    """
    t0 = time.time()
    
    search_query = ' & '.join(query.split())
    
    async with db.acquire() as conn:
        rows = await conn.fetch("""
            SELECT 
                id, pid, name, num_tracks, created_at,
                ts_rank(search_vector, to_tsquery('english', $1)) as rank
            FROM playlists
            WHERE user_id = $2
                AND search_vector @@ to_tsquery('english', $1)
            ORDER BY rank DESC, created_at DESC
            LIMIT $3 OFFSET $4
        """, search_query, current_user["id"], limit, offset)
        
        total_count = await conn.fetchval("""
            SELECT COUNT(*)
            FROM playlists
            WHERE user_id = $1
                AND search_vector @@ to_tsquery('english', $2)
        """, current_user["id"], search_query)
    
    playlists = [
        {
            "id": r["id"],
            "pid": r["pid"],
            "name": r["name"],
            "num_tracks": r["num_tracks"],
            "created_at": r["created_at"],
            "relevance_score": float(r["rank"])
        }
        for r in rows
    ]
    
    latency = int((time.time() - t0) * 1000)
    
    logger = ESLogger(es, background_tasks)
    logger.log_event(
        event_type="search",
        user_id=current_user["id"],
        query=query,
        result_count=len(playlists),
        total_count=total_count,
        latency_ms=latency
    )
    
    return {
        "query": query,
        "total_count": total_count,
        "result_count": len(playlists),
        "limit": limit,
        "offset": offset,
        "playlists": playlists,
        "latency_ms": latency
    }