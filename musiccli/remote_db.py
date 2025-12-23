# musiccli/remote_db.py
"""
Remote database module for querying Turso-hosted metadata.
Provides fallback when local Anna's Archive DB is not available.
"""

from typing import Optional, List, Dict

# libsql is imported lazily to avoid startup penalty if not needed
_libsql_module = None


def _get_libsql():
    """Lazy import of libsql."""
    global _libsql_module
    if _libsql_module is None:
        try:
            import libsql_experimental as libsql
            _libsql_module = libsql
        except ImportError:
            try:
                import libsql
                _libsql_module = libsql
            except ImportError:
                raise ImportError(
                    "libsql is required for remote database access. "
                    "Install with: pip install libsql-experimental"
                )
    return _libsql_module


# Default public read-only Turso database
DEFAULT_TURSO_URL = "libsql://musiccli-db-promaaa.turso.io"


def get_remote_connection(url: Optional[str] = None, token: Optional[str] = None):
    """
    Get a connection to the remote Turso database.
    
    Args:
        url: Turso database URL (uses default if not provided)
        token: Auth token (optional for public read-only DBs)
    
    Returns:
        libsql Connection object
    """
    from musiccli.config import load_config
    
    libsql = _get_libsql()
    config = load_config()
    
    # Use provided URL or config or default
    db_url = url or config.get("turso_url") or DEFAULT_TURSO_URL
    auth_token = token or config.get("turso_token")
    
    # Connect to remote database
    if auth_token:
        conn = libsql.connect(database=db_url, auth_token=auth_token)
    else:
        conn = libsql.connect(database=db_url)
    
    return conn


def search_tracks_remote(query: str, limit: int = 20) -> List[Dict]:
    """Search tracks in remote database."""
    try:
        conn = get_remote_connection()
        cursor = conn.execute("""
            SELECT id, name, artists, album_name, duration_ms, popularity, isrc
            FROM tracks
            WHERE name LIKE ?
            ORDER BY popularity DESC
            LIMIT ?
        """, (f"%{query}%", limit))
        
        columns = ['id', 'name', 'artists', 'album_name', 'duration_ms', 'popularity', 'isrc']
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as e:
        print(f"Remote DB error: {e}")
        return []


def search_artists_remote(query: str, limit: int = 20) -> List[Dict]:
    """Search artists in remote database."""
    try:
        conn = get_remote_connection()
        cursor = conn.execute("""
            SELECT id, name, popularity, followers_total
            FROM artists
            WHERE name LIKE ?
            ORDER BY followers_total DESC
            LIMIT ?
        """, (f"%{query}%", limit))
        
        columns = ['id', 'name', 'popularity', 'followers_total']
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as e:
        print(f"Remote DB error: {e}")
        return []


def search_albums_remote(query: str, limit: int = 20) -> List[Dict]:
    """Search albums in remote database."""
    try:
        conn = get_remote_connection()
        cursor = conn.execute("""
            SELECT id, name, album_type, release_date, popularity, total_tracks, artists
            FROM albums
            WHERE name LIKE ?
            ORDER BY popularity DESC
            LIMIT ?
        """, (f"%{query}%", limit))
        
        columns = ['id', 'name', 'album_type', 'release_date', 'popularity', 'total_tracks', 'artists']
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as e:
        print(f"Remote DB error: {e}")
        return []


def get_track_by_id_remote(track_id: str) -> Optional[Dict]:
    """Get a single track by ID from remote database."""
    try:
        conn = get_remote_connection()
        cursor = conn.execute("""
            SELECT id, name, artists, album_name, duration_ms, popularity, isrc
            FROM tracks
            WHERE id = ?
        """, (track_id,))
        
        row = cursor.fetchone()
        if row:
            columns = ['id', 'name', 'artists', 'album_name', 'duration_ms', 'popularity', 'isrc']
            return dict(zip(columns, row))
        return None
    except Exception as e:
        print(f"Remote DB error: {e}")
        return None


def get_tracks_by_ids_remote(track_ids: List[str]) -> Dict[str, Dict]:
    """Get multiple tracks by IDs from remote database."""
    if not track_ids:
        return {}
    
    try:
        conn = get_remote_connection()
        results = {}
        
        # Batch queries (Turso has limits on query complexity)
        batch_size = 100
        for i in range(0, len(track_ids), batch_size):
            batch = track_ids[i:i + batch_size]
            placeholders = ",".join("?" * len(batch))
            
            cursor = conn.execute(f"""
                SELECT id, name, artists, album_name, duration_ms, popularity, isrc
                FROM tracks
                WHERE id IN ({placeholders})
            """, batch)
            
            columns = ['id', 'name', 'artists', 'album_name', 'duration_ms', 'popularity', 'isrc']
            for row in cursor.fetchall():
                track = dict(zip(columns, row))
                results[track['id']] = track
        
        return results
    except Exception as e:
        print(f"Remote DB error: {e}")
        return {}


def is_remote_available() -> bool:
    """Check if remote database is accessible."""
    try:
        conn = get_remote_connection()
        conn.execute("SELECT 1")
        return True
    except Exception:
        return False
