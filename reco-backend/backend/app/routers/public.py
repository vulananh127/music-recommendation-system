from fastapi import APIRouter, Depends, Query
from dependencies import get_db

router = APIRouter()

@router.get("/tracks/popular")
async def get_popular_tracks(db = Depends(get_db)):
    # Helper function to clean whitespace from strings
    def clean_text(text):
        if not text:
            return text
        # Replace newlines and multiple spaces with single space
        return ' '.join(text.split())
    
    async with db.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                t.id,
                t.track_uri,
                t.track_name,
                a.artist_name,
                a.artist_uri,
                al.album_name,
                al.album_uri,
                t.duration_ms,
                tf.frequency
            FROM track_frequency tf
            JOIN tracks t ON tf.track_uri = t.track_uri
            JOIN artists a ON t.artist_id = a.id
            LEFT JOIN albums al ON t.album_id = al.id
            ORDER BY tf.frequency DESC
            LIMIT 10
        """)

        return [
            {
                "id": r["id"],
                "track_uri": r["track_uri"],
                "track_name": clean_text(r["track_name"]),
                "artist_name": clean_text(r["artist_name"]),
                "artist_uri": r["artist_uri"],
                "album_name": clean_text(r["album_name"]),
                "album_uri": r["album_uri"],
                "duration_ms": r["duration_ms"],
                "frequency": r["frequency"]
            }
            for r in rows
        ]

@router.get("/artists/popular")
async def get_popular_artist(db = Depends(get_db)):
    async with db.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT
                a.artist_uri,
                a.artist_name,
                SUM(tf.frequency) AS total_frequency
            FROM track_frequency tf
            JOIN tracks t ON tf.track_uri = t.track_uri
            JOIN artists a ON t.artist_id = a.id
            GROUP BY a.artist_uri, a.artist_name
            ORDER BY total_frequency DESC
            LIMIT 1
        """)

        if not row:
            return None

        return {
            "artist_uri": row["artist_uri"],
            "artist_name": row["artist_name"],
            "frequency": row["total_frequency"]
        }

@router.get("/artists/{artist_uri}/tracks")
async def get_tracks_by_artist(
    artist_uri: str,
    limit: int = Query(10, ge=1, le=100),
    db = Depends(get_db)
):
    # Helper function to clean whitespace from strings
    def clean_text(text):
        if not text:
            return text
        # Replace newlines and multiple spaces with single space
        return ' '.join(text.split())
    
    async with db.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                t.id,
                t.track_uri,
                t.track_name,
                a.artist_name,
                a.artist_uri,
                al.album_name,
                al.album_uri,
                t.duration_ms
            FROM tracks t
            JOIN artists a ON t.artist_id = a.id
            LEFT JOIN albums al ON t.album_id = al.id
            WHERE a.artist_uri = $1
            LIMIT $2
        """, artist_uri, limit)

        return [
            {
                "id": r["id"],
                "track_uri": r["track_uri"],
                "track_name": clean_text(r["track_name"]),
                "artist_name": clean_text(r["artist_name"]),
                "artist_uri": r["artist_uri"],
                "album_name": clean_text(r["album_name"]),
                "album_uri": r["album_uri"],
                "duration_ms": r["duration_ms"]
            }
            for r in rows
        ]
