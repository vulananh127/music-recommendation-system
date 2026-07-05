from fastapi import APIRouter, Query, Depends, BackgroundTasks
from typing import List
import time
from routers.auth import get_current_user
from dependencies import get_db, get_es
from logging_utils import ESLogger
from cache import get_cache, CacheStrategy, generate_cache_key
from pydantic import BaseModel

router = APIRouter()

class RecommendAllRequest(BaseModel):
    track_antecedents: List[str] = []
    artist_antecedents: List[str] = []
    limit: int = 10

class RecommendRequest(BaseModel):
    antecedents: List[str] = []
    limit: int = 10

@router.get("/recommend/tracks")
async def recommend_tracks(
    background_tasks: BackgroundTasks,
    antecedents: List[str] = Query(default=[], description="List of track URIs for recommendations"),
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    es = Depends(get_es)
):
    t0 = time.time()
    
    # Helper function to clean whitespace from strings
    def clean_text(text):
        if not text:
            return text
        # Replace newlines and multiple spaces with single space
        return ' '.join(text.split())
    
    cache = get_cache()
    cache_key = f"recommend:tracks:{generate_cache_key(*sorted(antecedents), limit=limit)}"
    
    cached_result = await cache.get(cache_key)
    if cached_result:
        latency = int((time.time() - t0) * 1000)
        
        logger = ESLogger(es, background_tasks)
        logger.log_event(
            event_type="recommendation_served",
            user_id=current_user["id"],
            rule_type="track",
            cache_hit=True,
            latency_ms=latency
        )
        
        cached_result["latency_ms"] = latency
        cached_result["from_cache"] = True
        return cached_result

    async with db.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, antecedents, consequents, confidence, lift, support
            FROM fp_rules_tracks
            WHERE antecedents && $1::text[]
            ORDER BY (confidence * lift) DESC
            LIMIT $2
        """, antecedents, limit)

        if not rows:
            return {"latency_ms": int((time.time() - t0) * 1000), "count": 0, "items": []}

        all_track_uris = []
        for r in rows:
            all_track_uris.extend(r["consequents"])
        
        unique_track_uris = list(set(all_track_uris))

        track_details_rows = await conn.fetch("""
            SELECT 
                t.id, t.track_uri, t.track_name, t.duration_ms,
                a.artist_name, a.artist_uri,
                al.album_name, al.album_uri
            FROM tracks t
            INNER JOIN artists a ON t.artist_id = a.id
            LEFT JOIN albums al ON t.album_id = al.id
            WHERE t.track_uri = ANY($1::text[])
        """, unique_track_uris)
        
        track_map = {
            t["track_uri"]: {
                "id": t["id"],
                "track_uri": t["track_uri"],
                "track_name": clean_text(t["track_name"]),
                "artist_name": clean_text(t["artist_name"]),
                "artist_uri": t["artist_uri"],
                "album_name": clean_text(t["album_name"]),
                "album_uri": t["album_uri"],
                "duration_ms": t["duration_ms"]
            } for t in track_details_rows
        }

        items = []
        for r in rows:
            consequents_with_details = [
                track_map[uri] for uri in r["consequents"] 
                if uri in track_map
            ]

            items.append({
                "rule_id": r["id"],
                "antecedents": r["antecedents"],
                "consequents": consequents_with_details,
                "score": float(r["confidence"] * r["lift"]),
                "confidence": float(r["confidence"]),
                "lift": float(r["lift"]),
                "support": float(r["support"]) if r["support"] is not None else None
            })

    latency = int((time.time() - t0) * 1000)
    
    result = {
        "latency_ms": latency, 
        "count": len(items), 
        "items": items,
        "from_cache": False
    }
    
    await cache.set(cache_key, result, ttl=CacheStrategy.RECOMMENDATIONS)

    logger = ESLogger(es, background_tasks)
    logger.log_event(
        event_type="recommendation_served",
        user_id=current_user["id"],
        rule_type="track",
        antecedents=antecedents,
        consequents=[[t["track_uri"] for t in x["consequents"]] for x in items],
        score=[x["score"] for x in items],
        cache_hit=False,
        latency_ms=latency
    )

    return result


@router.get("/recommend/artists")
async def recommend_artists(
    background_tasks: BackgroundTasks,
    antecedents: List[str] = Query(default=[], description="List of artist URIs for recommendations"),
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    es = Depends(get_es)
):
    t0 = time.time()
    
    # Helper function to clean whitespace from strings
    def clean_text(text):
        if not text:
            return text
        # Replace newlines and multiple spaces with single space
        return ' '.join(text.split())
    
    cache = get_cache()
    cache_key = f"recommend:artists:{generate_cache_key(*sorted(antecedents), limit=limit)}"
    
    cached_result = await cache.get(cache_key)
    if cached_result:
        latency = int((time.time() - t0) * 1000)
        
        logger = ESLogger(es, background_tasks)
        logger.log_event(
            event_type="recommendation_served",
            user_id=current_user["id"],
            rule_type="artist",
            cache_hit=True,
            latency_ms=latency
        )
        
        cached_result["latency_ms"] = latency
        cached_result["from_cache"] = True
        return cached_result
    
    async with db.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, antecedents, consequents, confidence, lift, support
            FROM fp_rules_artists
            WHERE antecedents && $1::text[]
            ORDER BY (confidence * lift) DESC
            LIMIT $2
        """, antecedents, limit)

        if not rows:
            return {"latency_ms": int((time.time() - t0) * 1000), "count": 0, "items": []}

        all_artist_uris = []
        for r in rows:
            all_artist_uris.extend(r["consequents"])
        
        unique_artist_uris = list(set(all_artist_uris))

        # FIXED: Added t.id to SELECT and JOIN with tracks table
        top_tracks_rows = await conn.fetch("""
            SELECT t.id, t.duration_ms, tf.track_uri, tf.track_name, tf.artist_name, tf.artist_uri, tf.frequency
            FROM (
                SELECT 
                    track_uri, track_name, artist_name, artist_uri, frequency,
                    ROW_NUMBER() OVER (PARTITION BY artist_uri ORDER BY frequency DESC) as rn
                FROM track_frequency
                WHERE artist_uri = ANY($1::text[])
            ) tf
            INNER JOIN tracks t ON t.track_uri = tf.track_uri
            WHERE tf.rn <= 3
            ORDER BY tf.artist_uri, tf.frequency DESC
        """, unique_artist_uris)

        artist_tracks_map = {}
        for track in top_tracks_rows:
            artist_uri = track["artist_uri"]
            if artist_uri not in artist_tracks_map:
                artist_tracks_map[artist_uri] = []
            artist_tracks_map[artist_uri].append({
                "id": track["id"],  # ✅ ADDED
                "track_uri": track["track_uri"],
                "track_name": clean_text(track["track_name"]),
                "artist_name": clean_text(track["artist_name"]),
                "duration_ms": track["duration_ms"],
                "frequency": track["frequency"]
            })

        items = []
        for r in rows:
            items.append({
                "rule_id": r["id"],
                "antecedents": r["antecedents"],
                "consequents": r["consequents"],
                "score": float(r["confidence"] * r["lift"]),
                "confidence": float(r["confidence"]),
                "lift": float(r["lift"]),
                "support": float(r["support"]) if r["support"] is not None else None,
                "top_tracks": [
                    track for artist_uri in r["consequents"]
                    for track in artist_tracks_map.get(artist_uri, [])
                ]
            })

    latency = int((time.time() - t0) * 1000)
    
    result = {
        "latency_ms": latency, 
        "count": len(items), 
        "items": items,
        "from_cache": False
    }
    
    await cache.set(cache_key, result, ttl=CacheStrategy.RECOMMENDATIONS)

    logger = ESLogger(es, background_tasks)
    logger.log_event(
        event_type="recommendation_served",
        user_id=current_user["id"],
        rule_type="artist",
        antecedents=antecedents,
        consequents=[x["consequents"] for x in items],
        score=[x["score"] for x in items],
        cache_hit=False,
        latency_ms=latency
    )

    return result 

@router.get("/recommend/all")
async def recommend_all(
    background_tasks: BackgroundTasks,
    track_antecedents: List[str] = Query(default=[], description="List of track URIs for recommendations"),
    artist_antecedents: List[str] = Query(default=[], description="List of artist URIs for recommendations"),
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    es = Depends(get_es)
):
    t0 = time.time()
    
    # Helper function to clean whitespace from strings
    def clean_text(text):
        if not text:
            return text
        # Replace newlines and multiple spaces with single space
        return ' '.join(text.split())
    
    cache = get_cache()
    cache_key = f"recommend:all:{generate_cache_key(*sorted(track_antecedents), *sorted(artist_antecedents), limit=limit)}"

    cached_result = await cache.get(cache_key)
    if cached_result:
        latency = int((time.time() - t0) * 1000)
        cached_result["latency_ms"] = latency
        cached_result["from_cache"] = True
        return cached_result

    async with db.acquire() as conn:
        # --- TRACK RECOMMENDATIONS ---
        track_rows = await conn.fetch("""
            SELECT id, antecedents, antecedent_names, consequents, consequent_names, confidence, lift, support
            FROM fp_rules_tracks
            WHERE antecedents && $1::text[]
            ORDER BY (confidence * lift) DESC
            LIMIT $2
        """, track_antecedents, limit)

        track_items = []
        if track_rows:
            all_track_uris = []
            for r in track_rows:
                all_track_uris.extend(r["consequents"])
            unique_track_uris = list(set(all_track_uris))

            track_details_rows = await conn.fetch("""
                SELECT 
                    t.id, t.track_uri, t.track_name, t.duration_ms,
                    a.artist_name, a.artist_uri,
                    al.album_name, al.album_uri
                FROM tracks t
                INNER JOIN artists a ON t.artist_id = a.id
                LEFT JOIN albums al ON t.album_id = al.id
                WHERE t.track_uri = ANY($1::text[])
            """, unique_track_uris)

            track_map = {
                t["track_uri"]: {
                    "id": t["id"],
                    "track_uri": t["track_uri"],
                    "track_name": clean_text(t["track_name"]),
                    "artist_name": clean_text(t["artist_name"]),
                    "artist_uri": t["artist_uri"],
                    "album_name": clean_text(t["album_name"]),
                    "album_uri": t["album_uri"],
                    "duration_ms": t["duration_ms"]
                } for t in track_details_rows
            }

            for r in track_rows:
                consequents_with_details = [
                    track_map[uri] for uri in r["consequents"] if uri in track_map
                ]
                track_items.append({
                    "rule_id": r["id"],
                    "antecedents": r["antecedents"],
                    "antecedent_names": r["antecedent_names"],   
                    "consequents": consequents_with_details,
                    "consequent_names": r["consequent_names"],   
                    "score": float(r["confidence"] * r["lift"]),
                    "confidence": float(r["confidence"]),
                    "lift": float(r["lift"]),
                    "support": float(r["support"]) if r["support"] is not None else None
                })

        # --- ARTIST RECOMMENDATIONS ---
        artist_rows = await conn.fetch("""
            SELECT id, antecedents, antecedent_names, consequents, consequent_names, confidence, lift, support
            FROM fp_rules_artists
            WHERE antecedents && $1::text[]
            ORDER BY (confidence * lift) DESC
            LIMIT $2
        """, artist_antecedents, limit)

        artist_items = []
        if artist_rows:
            all_artist_uris = []
            for r in artist_rows:
                all_artist_uris.extend(r["consequents"])
            unique_artist_uris = list(set(all_artist_uris))

            top_tracks_rows = await conn.fetch("""
                SELECT t.id, t.duration_ms, tf.track_uri, tf.track_name, tf.artist_name, tf.artist_uri, tf.frequency
                FROM (
                    SELECT 
                        track_uri, track_name, artist_name, artist_uri, frequency,
                        ROW_NUMBER() OVER (PARTITION BY artist_uri ORDER BY frequency DESC) as rn
                    FROM track_frequency
                    WHERE artist_uri = ANY($1::text[])
                ) tf
                INNER JOIN tracks t ON t.track_uri = tf.track_uri
                WHERE tf.rn <= 3
                ORDER BY tf.artist_uri, tf.frequency DESC
            """, unique_artist_uris)

            artist_tracks_map = {}
            for track in top_tracks_rows:
                artist_tracks_map.setdefault(track["artist_uri"], []).append({
                    "id": track["id"],
                    "track_uri": track["track_uri"],
                    "track_name": clean_text(track["track_name"]),
                    "artist_name": clean_text(track["artist_name"]),
                    "duration_ms": track["duration_ms"],
                    "frequency": track["frequency"]
                })

            for r in artist_rows:
                artist_items.append({
                    "rule_id": r["id"],
                    "antecedents": r["antecedents"],
                    "antecedent_names": r["antecedent_names"],   
                    "consequents": r["consequents"],
                    "consequent_names": r["consequent_names"],   
                    "score": float(r["confidence"] * r["lift"]),
                    "confidence": float(r["confidence"]),
                    "lift": float(r["lift"]),
                    "support": float(r["support"]) if r["support"] is not None else None,
                    "top_tracks": [
                        track for artist_uri in r["consequents"]
                        for track in artist_tracks_map.get(artist_uri, [])
                    ]
                })

    latency = int((time.time() - t0) * 1000)
    result = {
        "latency_ms": latency,
        "track_recommendations": {
            "count": len(track_items),
            "items": track_items
        },
        "artist_recommendations": {
            "count": len(artist_items),
            "items": artist_items
        },
        "from_cache": False
    }

    await cache.set(cache_key, result, ttl=CacheStrategy.RECOMMENDATIONS)

    return result 

@router.post("/recommend/tracks")
async def recommend_tracks_post(
    request: RecommendRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    es = Depends(get_es)
):
    return await recommend_tracks(
        background_tasks=background_tasks, 
        antecedents=request.antecedents, 
        limit=request.limit, 
        current_user=current_user, 
        db=db, 
        es=es
    )

@router.post("/recommend/artists")
async def recommend_artists_post(
    request: RecommendRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    es = Depends(get_es)
):
    return await recommend_artists(
        background_tasks=background_tasks, 
        antecedents=request.antecedents, 
        limit=request.limit, 
        current_user=current_user, 
        db=db, 
        es=es
    )

@router.post("/recommend/all")
async def recommend_all_post(
    request: RecommendAllRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    es = Depends(get_es)
):
    return await recommend_all(
        background_tasks=background_tasks, 
        track_antecedents=request.track_antecedents, 
        artist_antecedents=request.artist_antecedents, 
        limit=request.limit, 
        current_user=current_user, 
        db=db, 
        es=es
    )
