# musiccli/db.py
"""
Database module for querying Anna's Archive Spotify metadata.
Supports both local SQLite and remote Turso databases.
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict
from musiccli.config import load_config


def _has_local_db() -> bool:
    """Check if local database is configured and exists."""
    config = load_config()
    db_path = config.get("db_path")
    if not db_path:
        return False
    return Path(db_path).exists()


def get_db_connection(db_name: str = "main") -> sqlite3.Connection:
    """
    Get a connection to the specified database.
    db_name: "main" for spotify_clean.sqlite3, "files" for track_files
    """
    config = load_config()
    
    if db_name == "main":
        db_path = config.get("db_path")
        if not db_path:
            raise FileNotFoundError(
                "Database path not configured. Run: musiccli setup --db-path /path/to/spotify_clean.sqlite3"
            )
    else:
        db_path = config.get("track_files_db_path")
        if not db_path:
            return None
    
    path = Path(db_path)
    if not path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def search_tracks(query: str, limit: int = 20) -> List[Dict]:
    """Search tracks by name, ordered by popularity. Uses local DB or remote fallback."""
    # Try local DB first
    if _has_local_db():
        return _search_tracks_local(query, limit)
    
    # Fallback to remote Turso DB
    try:
        from musiccli.remote_db import search_tracks_remote
        return search_tracks_remote(query, limit)
    except ImportError:
        raise FileNotFoundError(
            "No database available. Either:\n"
            "  1. Configure local DB: musiccli setup --db-path /path/to/db\n"
            "  2. Install libsql: pip install libsql-experimental"
        )


def _search_tracks_local(query: str, limit: int = 20) -> List[Dict]:
    """Search tracks in local database."""
    conn = get_db_connection("main")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            t.id,
            t.name,
            t.popularity,
            t.duration_ms,
            t.external_id_isrc as isrc,
            a.name as album_name,
            a.id as album_id,
            GROUP_CONCAT(ar.name, ', ') as artists
        FROM tracks t
        JOIN albums a ON t.album_rowid = a.rowid
        LEFT JOIN track_artists ta ON ta.track_rowid = t.rowid
        LEFT JOIN artists ar ON ta.artist_rowid = ar.rowid
        WHERE t.name LIKE ?
        GROUP BY t.id
        ORDER BY t.popularity DESC
        LIMIT ?
    """, (f"%{query}%", limit))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def search_artists(query: str, limit: int = 20) -> list[dict]:
    """Search artists by name, ordered by followers."""
    conn = get_db_connection("main")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            id,
            name,
            popularity,
            followers_total
        FROM artists
        WHERE name LIKE ?
        ORDER BY followers_total DESC
        LIMIT ?
    """, (f"%{query}%", limit))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def search_albums(query: str, limit: int = 20) -> list[dict]:
    """Search albums by name, ordered by popularity."""
    conn = get_db_connection("main")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            al.id,
            al.name,
            al.album_type,
            al.release_date,
            al.popularity,
            al.total_tracks,
            GROUP_CONCAT(ar.name, ', ') as artists
        FROM albums al
        LEFT JOIN artist_albums aa ON aa.album_rowid = al.rowid
        LEFT JOIN artists ar ON aa.artist_rowid = ar.rowid
        WHERE al.name LIKE ?
        GROUP BY al.id
        ORDER BY al.popularity DESC
        LIMIT ?
    """, (f"%{query}%", limit))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_track_details(track_id: str) -> Optional[dict]:
    """Get full details for a single track."""
    conn = get_db_connection("main")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            t.id,
            t.name,
            t.popularity,
            t.duration_ms,
            t.external_id_isrc as isrc,
            t.explicit,
            t.disc_number,
            t.track_number,
            a.id as album_id,
            a.name as album_name,
            a.release_date,
            a.album_type
        FROM tracks t
        JOIN albums a ON t.album_rowid = a.rowid
        WHERE t.id = ?
    """, (track_id,))
    
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    
    track = dict(row)
    
    # Get artists
    cursor.execute("""
        SELECT ar.id, ar.name
        FROM track_artists ta
        JOIN artists ar ON ta.artist_rowid = ar.rowid
        JOIN tracks t ON ta.track_rowid = t.rowid
        WHERE t.id = ?
    """, (track_id,))
    
    track["artists"] = [dict(r) for r in cursor.fetchall()]
    conn.close()
    
    # Get file info if available
    file_info = get_track_file_info(track_id)
    if file_info:
        track["file_info"] = file_info
    
    return track


def get_artist_details(artist_id: str) -> Optional[dict]:
    """Get full details for an artist including their albums."""
    conn = get_db_connection("main")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, popularity, followers_total
        FROM artists WHERE id = ?
    """, (artist_id,))
    
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    
    artist = dict(row)
    
    # Get genres
    cursor.execute("""
        SELECT genre FROM artist_genres ag
        JOIN artists a ON ag.artist_rowid = a.rowid
        WHERE a.id = ?
    """, (artist_id,))
    artist["genres"] = [r["genre"] for r in cursor.fetchall()]
    
    # Get albums
    cursor.execute("""
        SELECT al.id, al.name, al.album_type, al.release_date, al.popularity
        FROM albums al
        JOIN artist_albums aa ON aa.album_rowid = al.rowid
        JOIN artists ar ON aa.artist_rowid = ar.rowid
        WHERE ar.id = ?
        ORDER BY al.release_date DESC
        LIMIT 20
    """, (artist_id,))
    artist["albums"] = [dict(r) for r in cursor.fetchall()]
    
    conn.close()
    return artist


def get_album_details(album_id: str) -> Optional[dict]:
    """Get full details for an album including tracks."""
    conn = get_db_connection("main")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            id, name, album_type, release_date, 
            popularity, total_tracks, label,
            external_id_upc as upc
        FROM albums WHERE id = ?
    """, (album_id,))
    
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    
    album = dict(row)
    
    # Get artists
    cursor.execute("""
        SELECT ar.id, ar.name
        FROM artist_albums aa
        JOIN artists ar ON aa.artist_rowid = ar.rowid
        JOIN albums al ON aa.album_rowid = al.rowid
        WHERE al.id = ?
    """, (album_id,))
    album["artists"] = [dict(r) for r in cursor.fetchall()]
    
    # Get tracks
    cursor.execute("""
        SELECT t.id, t.name, t.duration_ms, t.popularity, t.track_number, t.disc_number
        FROM tracks t
        JOIN albums a ON t.album_rowid = a.rowid
        WHERE a.id = ?
        ORDER BY t.disc_number, t.track_number
    """, (album_id,))
    album["tracks"] = [dict(r) for r in cursor.fetchall()]
    
    conn.close()
    return album


def get_track_file_info(track_id: str) -> Optional[dict]:
    """Get file info from track_files database."""
    try:
        conn = get_db_connection("files")
        if not conn:
            return None
    except FileNotFoundError:
        return None
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            filename,
            status,
            track_popularity,
            sha256_with_embedded_meta,
            reencoded_kbit_vbr
        FROM track_files
        WHERE track_id = ?
    """, (track_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def get_tracks_by_ids(track_ids: List[str]) -> Dict[str, Dict]:
    """
    Get multiple tracks by their Spotify IDs.
    Returns a dict mapping track_id -> track_data.
    Uses local DB or remote fallback.
    """
    if not track_ids:
        return {}
    
    # Try local DB first
    if _has_local_db():
        return _get_tracks_by_ids_local(track_ids)
    
    # Fallback to remote Turso DB
    try:
        from musiccli.remote_db import get_tracks_by_ids_remote
        return get_tracks_by_ids_remote(track_ids)
    except ImportError:
        return {}


def _get_tracks_by_ids_local(track_ids: List[str]) -> Dict[str, Dict]:
    """Get multiple tracks from local database."""
    conn = get_db_connection("main")
    cursor = conn.cursor()
    
    # SQLite has a limit on placeholders, batch if needed
    results = {}
    batch_size = 500
    
    for i in range(0, len(track_ids), batch_size):
        batch = track_ids[i:i + batch_size]
        placeholders = ",".join("?" * len(batch))
        
        cursor.execute(f"""
            SELECT 
                t.id,
                t.name,
                t.popularity,
                t.duration_ms,
                t.external_id_isrc as isrc,
                a.name as album_name,
                a.id as album_id,
                GROUP_CONCAT(ar.name, ', ') as artists
            FROM tracks t
            JOIN albums a ON t.album_rowid = a.rowid
            LEFT JOIN track_artists ta ON ta.track_rowid = t.rowid
            LEFT JOIN artists ar ON ta.artist_rowid = ar.rowid
            WHERE t.id IN ({placeholders})
            GROUP BY t.id
        """, batch)
        
        for row in cursor.fetchall():
            results[row["id"]] = dict(row)
    
    conn.close()
    return results


def get_tracks_file_info_batch(track_ids: list[str]) -> dict[str, dict]:
    """
    Get file info for multiple tracks.
    Returns a dict mapping track_id -> file_info.
    """
    if not track_ids:
        return {}
    
    try:
        conn = get_db_connection("files")
        if not conn:
            return {}
    except FileNotFoundError:
        return {}
    
    cursor = conn.cursor()
    results = {}
    batch_size = 500
    
    for i in range(0, len(track_ids), batch_size):
        batch = track_ids[i:i + batch_size]
        placeholders = ",".join("?" * len(batch))
        
        cursor.execute(f"""
            SELECT 
                track_id,
                filename,
                status,
                track_popularity,
                sha256_with_embedded_meta,
                reencoded_kbit_vbr
            FROM track_files
            WHERE track_id IN ({placeholders})
        """, batch)
        
        for row in cursor.fetchall():
            results[row["track_id"]] = dict(row)
    
    conn.close()
    return results

