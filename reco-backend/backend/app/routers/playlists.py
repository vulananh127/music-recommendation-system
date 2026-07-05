from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import time
from routers.auth import get_current_user
from dependencies import get_db, get_es

router = APIRouter()

class PlaylistCreate(BaseModel):
    name: str

class PlaylistUpdate(BaseModel):
    name: Optional[str] = None

class PlaylistResponse(BaseModel):
    id: int
    pid: str
    user_id: str
    name: str
    num_tracks: Optional[int]
    created_at: datetime

class PlaylistDetailResponse(PlaylistResponse):
    tracks: List[dict]

@router.post("/playlists", response_model=PlaylistResponse)
async def create_playlist(
    playlist_data: PlaylistCreate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    es = Depends(get_es)
):
    """Tạo playlist mới"""
    t0 = time.time()
    
    async with db.acquire() as conn:
        # Tạo pid unique
        pid = f"user_{current_user['id']}_{int(time.time())}"
        
        playlist_id = await conn.fetchval(
            """
            INSERT INTO playlists (pid, user_id, name, num_tracks, actual_track_count)
            VALUES ($1, $2, $3, 0, 0)
            RETURNING id
            """,
            pid, current_user["id"], playlist_data.name
        )
        
        playlist = await conn.fetchrow(
            """
            SELECT id, pid, user_id, name, num_tracks, created_at
            FROM playlists WHERE id = $1
            """,
            playlist_id
        )
    
    latency = int((time.time() - t0) * 1000)
    
    # Log event
    try:
        await es.post("/analytics/_doc", json={
            "timestamp": int(time.time() * 1000),
            "event_type": "playlist_create",
            "user_id": current_user["id"],
            "playlist_id": playlist_id,
            "playlist_name": playlist_data.name,
            "latency_ms": latency
        })
    except:
        pass
    
    return {
        "id": playlist["id"],
        "pid": playlist["pid"],
        "user_id": str(playlist["user_id"]),
        "name": playlist["name"],
        "num_tracks": playlist["num_tracks"],
        "created_at": playlist["created_at"]
    }

@router.get("/playlists", response_model=List[PlaylistResponse])
async def get_playlists(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    es = Depends(get_es)
):
    """Lấy danh sách playlist của user"""
    t0 = time.time()
    
    async with db.acquire() as conn:
        playlists = await conn.fetch(
            """
            SELECT id, pid, user_id, name, num_tracks, created_at
            FROM playlists
            WHERE user_id = $1
            ORDER BY created_at DESC
            """,
            current_user["id"]
        )
    
    latency = int((time.time() - t0) * 1000)
    
    # Log event
    try:
        await es.post("/analytics/_doc", json={
            "timestamp": int(time.time() * 1000),
            "event_type": "playlist_list",
            "user_id": current_user["id"],
            "count": len(playlists),
            "latency_ms": latency
        })
    except:
        pass
    
    return [
        {
            "id": p["id"],
            "pid": p["pid"],
            "user_id": str(p["user_id"]),
            "name": p["name"],
            "num_tracks": p["num_tracks"],
            "created_at": p["created_at"]
        }
        for p in playlists
    ]

@router.get("/playlists/{playlist_id}", response_model=PlaylistDetailResponse)
async def get_playlist(
    playlist_id: int,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    es = Depends(get_es)
):
    """Lấy chi tiết playlist"""
    t0 = time.time()
    
    # Helper function to clean whitespace from strings
    def clean_text(text):
        if not text:
            return text
        # Replace newlines and multiple spaces with single space
        return ' '.join(text.split())
    
    async with db.acquire() as conn:
        playlist = await conn.fetchrow(
            """
            SELECT id, pid, user_id, name, num_tracks, created_at
            FROM playlists
            WHERE id = $1 AND user_id = $2
            """,
            playlist_id, current_user["id"]
        )
        
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")
        
        # Lấy danh sách tracks
        tracks = await conn.fetch(
            """
            SELECT 
                t.id, t.track_uri, t.track_name, t.duration_ms,
                a.artist_name, a.artist_uri,
                al.album_name, al.album_uri,
                pt.pos, pt.added_at
            FROM playlist_tracks pt
            JOIN tracks t ON pt.track_id = t.id
            LEFT JOIN artists a ON t.artist_id = a.id
            LEFT JOIN albums al ON t.album_id = al.id
            WHERE pt.playlist_id = $1
            ORDER BY pt.pos ASC
            """,
            playlist_id
        )
    
    latency = int((time.time() - t0) * 1000)
    
    # Log event
    try:
        await es.post("/analytics/_doc", json={
            "timestamp": int(time.time() * 1000),
            "event_type": "playlist_view",
            "user_id": current_user["id"],
            "playlist_id": playlist_id,
            "track_count": len(tracks),
            "latency_ms": latency
        })
    except:
        pass
    
    return {
        "id": playlist["id"],
        "pid": playlist["pid"],
        "user_id": str(playlist["user_id"]),
        "name": playlist["name"],
        "num_tracks": playlist["num_tracks"],
        "created_at": playlist["created_at"],
        "tracks": [
            {
                "id": t["id"],
                "track_uri": t["track_uri"],
                "track_name": clean_text(t["track_name"]),
                "artist_name": clean_text(t["artist_name"]),
                "artist_uri": t["artist_uri"],
                "album_name": clean_text(t["album_name"]),
                "album_uri": t["album_uri"],
                "duration_ms": t["duration_ms"],
                "pos": t["pos"],
                "added_at": t["added_at"]
            }
            for t in tracks
        ]
    }

@router.put("/playlists/{playlist_id}", response_model=PlaylistResponse)
async def update_playlist(
    playlist_id: int,
    playlist_data: PlaylistUpdate,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    es = Depends(get_es)
):
    """Cập nhật playlist"""
    t0 = time.time()
    
    async with db.acquire() as conn:
        # Kiểm tra quyền sở hữu
        playlist = await conn.fetchrow(
            "SELECT id FROM playlists WHERE id = $1 AND user_id = $2",
            playlist_id, current_user["id"]
        )
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")
        
        # Cập nhật
        update_fields = []
        params = []
        param_idx = 1
        
        if playlist_data.name is not None:
            update_fields.append(f"name = ${param_idx}")
            params.append(playlist_data.name)
            param_idx += 1
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        params.append(playlist_id)
        params.append(current_user["id"])
        
        await conn.execute(
            f"""
            UPDATE playlists
            SET {', '.join(update_fields)}
            WHERE id = ${param_idx} AND user_id = ${param_idx + 1}
            """,
            *params
        )
        
        updated = await conn.fetchrow(
            """
            SELECT id, pid, user_id, name, num_tracks, created_at
            FROM playlists WHERE id = $1
            """,
            playlist_id
        )
    
    latency = int((time.time() - t0) * 1000)
    
    # Log event
    try:
        await es.post("/analytics/_doc", json={
            "timestamp": int(time.time() * 1000),
            "event_type": "playlist_update",
            "user_id": current_user["id"],
            "playlist_id": playlist_id,
            "latency_ms": latency
        })
    except:
        pass
    
    return {
        "id": updated["id"],
        "pid": updated["pid"],
        "user_id": str(updated["user_id"]),
        "name": updated["name"],
        "num_tracks": updated["num_tracks"],
        "created_at": updated["created_at"]
    }

@router.delete("/playlists/{playlist_id}")
async def delete_playlist(
    playlist_id: int,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    es = Depends(get_es)
):
    """Xóa playlist"""
    t0 = time.time()
    
    async with db.acquire() as conn:
        # Kiểm tra quyền sở hữu
        playlist = await conn.fetchrow(
            "SELECT id FROM playlists WHERE id = $1 AND user_id = $2",
            playlist_id, current_user["id"]
        )
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")
        
        # Xóa (cascade sẽ xóa playlist_tracks)
        await conn.execute(
            "DELETE FROM playlists WHERE id = $1",
            playlist_id
        )
    
    latency = int((time.time() - t0) * 1000)
    
    # Log event
    try:
        await es.post("/analytics/_doc", json={
            "timestamp": int(time.time() * 1000),
            "event_type": "playlist_delete",
            "user_id": current_user["id"],
            "playlist_id": playlist_id,
            "latency_ms": latency
        })
    except:
        pass
    
    return {"status": "ok", "message": "Playlist deleted successfully"}

