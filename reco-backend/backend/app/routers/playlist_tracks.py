from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import time
from routers.auth import get_current_user
from dependencies import get_db, get_es

router = APIRouter()

class AddTrackRequest(BaseModel):
    track_id: int
    position: Optional[int] = None  

class RemoveTrackRequest(BaseModel):
    track_id: int

@router.post("/playlists/{playlist_id}/tracks")
async def add_track_to_playlist(
    playlist_id: int,
    track_data: AddTrackRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    es = Depends(get_es)
):
    """Thêm bài hát vào playlist"""
    t0 = time.time()
    
    async with db.acquire() as conn:
        # Kiểm tra quyền sở hữu playlist
        playlist = await conn.fetchrow(
            "SELECT id FROM playlists WHERE id = $1 AND user_id = $2",
            playlist_id, current_user["id"]
        )
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")
        
        # Kiểm tra track tồn tại
        track = await conn.fetchrow(
            "SELECT id FROM tracks WHERE id = $1",
            track_data.track_id
        )
        if not track:
            raise HTTPException(status_code=404, detail="Track not found")
        
        # Kiểm tra track đã có trong playlist chưa
        existing = await conn.fetchrow(
            "SELECT id FROM playlist_tracks WHERE playlist_id = $1 AND track_id = $2",
            playlist_id, track_data.track_id
        )
        if existing:
            raise HTTPException(status_code=400, detail="Track already in playlist")
        
        # Xác định vị trí
        if track_data.position is None:
            max_pos = await conn.fetchval(
                "SELECT COALESCE(MAX(pos), 0) FROM playlist_tracks WHERE playlist_id = $1",
                playlist_id
            )
            position = max_pos + 1
        else:
            position = track_data.position
            # Dịch chuyển các track sau vị trí này
            await conn.execute(
                """
                UPDATE playlist_tracks
                SET pos = pos + 1
                WHERE playlist_id = $1 AND pos >= $2
                """,
                playlist_id, position
            )
        
        # Thêm track
        await conn.execute(
            """
            INSERT INTO playlist_tracks (playlist_id, track_id, pos)
            VALUES ($1, $2, $3)
            """,
            playlist_id, track_data.track_id, position
        )
        
        # Cập nhật số lượng tracks
        await conn.execute(
            """
            UPDATE playlists
            SET num_tracks = (SELECT COUNT(*) FROM playlist_tracks WHERE playlist_id = $1),
                actual_track_count = (SELECT COUNT(*) FROM playlist_tracks WHERE playlist_id = $1)
            WHERE id = $1
            """,
            playlist_id
        )
    
    latency = int((time.time() - t0) * 1000)
    
    # Log event
    try:
        await es.post("/analytics/_doc", json={
            "timestamp": int(time.time() * 1000),
            "event_type": "playlist_track_add",
            "user_id": current_user["id"],
            "playlist_id": playlist_id,
            "track_id": track_data.track_id,
            "position": position,
            "latency_ms": latency
        })
    except:
        pass
    
    return {"status": "ok", "message": "Track added to playlist", "position": position}

@router.delete("/playlists/{playlist_id}/tracks/{track_id}")
async def remove_track_from_playlist(
    playlist_id: int,
    track_id: int,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    es = Depends(get_es)
):
    """Xóa bài hát khỏi playlist"""
    t0 = time.time()
    
    async with db.acquire() as conn:
        # Kiểm tra quyền sở hữu playlist
        playlist = await conn.fetchrow(
            "SELECT id FROM playlists WHERE id = $1 AND user_id = $2",
            playlist_id, current_user["id"]
        )
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")
        
        # Lấy vị trí của track
        track_pos = await conn.fetchval(
            "SELECT pos FROM playlist_tracks WHERE playlist_id = $1 AND track_id = $2",
            playlist_id, track_id
        )
        if track_pos is None:
            raise HTTPException(status_code=404, detail="Track not found in playlist")
        
        # Xóa track
        await conn.execute(
            "DELETE FROM playlist_tracks WHERE playlist_id = $1 AND track_id = $2",
            playlist_id, track_id
        )
        
        # Dịch chuyển các track sau vị trí này
        await conn.execute(
            """
            UPDATE playlist_tracks
            SET pos = pos - 1
            WHERE playlist_id = $1 AND pos > $2
            """,
            playlist_id, track_pos
        )
        
        # Cập nhật số lượng tracks
        await conn.execute(
            """
            UPDATE playlists
            SET num_tracks = (SELECT COUNT(*) FROM playlist_tracks WHERE playlist_id = $1),
                actual_track_count = (SELECT COUNT(*) FROM playlist_tracks WHERE playlist_id = $1)
            WHERE id = $1
            """,
            playlist_id
        )
    
    latency = int((time.time() - t0) * 1000)
    
    # Log event
    try:
        await es.post("/analytics/_doc", json={
            "timestamp": int(time.time() * 1000),
            "event_type": "playlist_track_remove",
            "user_id": current_user["id"],
            "playlist_id": playlist_id,
            "track_id": track_id,
            "latency_ms": latency
        })
    except:
        pass
    
    return {"status": "ok", "message": "Track removed from playlist"}