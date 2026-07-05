from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
import time
from routers.auth import get_current_user
from dependencies import get_db, get_es

router = APIRouter()

class ClickEvent(BaseModel):
    item_id: str         # track_uri or artist_uri
    item_type: str = "track"  # track or artist
    rule_id: Optional[int] = None
    rule_type: Optional[str] = None   # track or artist
    playlist_id: Optional[int] = None
    context: Optional[dict] = None

class ViewEvent(BaseModel):
    item_id: str
    item_type: str = "track"  # track, artist, album, playlist
    context: Optional[dict] = None

@router.post("/events/click")
async def click_event(
    e: ClickEvent,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    es = Depends(get_es)
):
    """Ghi lại sự kiện click (CTR tracking)"""
    try:
        await es.post("/analytics/_doc", json={
            "timestamp": int(time.time() * 1000),
            "event_type": "click",
            "user_id": current_user["id"],
            "item_id": e.item_id,
            "item_type": e.item_type,
            "rule_id": e.rule_id,
            "rule_type": e.rule_type,
            "playlist_id": e.playlist_id,
            "context": e.context or {}
        })
    except Exception as ex:
        # Log lỗi nhưng không fail request
        print(f"Error logging click event: {ex}")
    
    return {"status": "ok", "message": "Click event logged"}

@router.post("/events/view")
async def view_event(
    e: ViewEvent,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db),
    es = Depends(get_es)
):
    """Ghi lại sự kiện xem"""
    try:
        await es.post("/analytics/_doc", json={
            "timestamp": int(time.time() * 1000),
            "event_type": "view",
            "user_id": current_user["id"],
            "item_id": e.item_id,
            "item_type": e.item_type,
            "context": e.context or {}
        })
    except Exception as ex:
        print(f"Error logging view event: {ex}")
    
    return {"status": "ok", "message": "View event logged"}