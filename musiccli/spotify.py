# musiccli/spotify.py
"""
Spotify playlist handling for MusicCLI.
Supports both local database lookup and Spotify API.
"""

import re
import base64
from typing import Optional, Tuple, List, Dict
from urllib.parse import urlparse

import requests

from musiccli.config import load_config


# Spotify URL patterns
SPOTIFY_URL_PATTERNS = [
    # open.spotify.com/playlist/ID
    r'open\.spotify\.com/(playlist|album|track)/([a-zA-Z0-9]+)',
    # spotify:playlist:ID
    r'spotify:(playlist|album|track):([a-zA-Z0-9]+)',
]


def parse_spotify_url(url: str) -> Optional[Tuple[str, str]]:
    """
    Parse a Spotify URL or URI and extract the type and ID.
    
    Returns:
        tuple of (type, id) where type is 'playlist', 'album', or 'track'
        None if URL is invalid
    """
    for pattern in SPOTIFY_URL_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1), match.group(2)
    return None


class SpotifyAPI:
    """Spotify Web API client for fetching playlist data."""
    
    TOKEN_URL = "https://accounts.spotify.com/api/token"
    API_BASE = "https://api.spotify.com/v1"
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token = None
    
    def _get_access_token(self) -> str:
        """Get or refresh access token using client credentials flow."""
        if self._access_token:
            return self._access_token
        
        auth_str = f"{self.client_id}:{self.client_secret}"
        auth_b64 = base64.b64encode(auth_str.encode()).decode()
        
        response = requests.post(
            self.TOKEN_URL,
            headers={"Authorization": f"Basic {auth_b64}"},
            data={"grant_type": "client_credentials"},
            timeout=10
        )
        response.raise_for_status()
        
        self._access_token = response.json()["access_token"]
        return self._access_token
    
    def _api_request(self, endpoint: str, params: dict = None) -> dict:
        """Make an authenticated API request."""
        token = self._get_access_token()
        response = requests.get(
            f"{self.API_BASE}{endpoint}",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=15
        )
        response.raise_for_status()
        return response.json()
    
    def get_playlist(self, playlist_id: str) -> dict:
        """Fetch playlist metadata."""
        return self._api_request(f"/playlists/{playlist_id}")
    
    def get_playlist_tracks(self, playlist_id: str) -> List[Dict]:
        """Fetch all tracks from a playlist (handles pagination)."""
        tracks = []
        offset = 0
        limit = 100
        
        while True:
            data = self._api_request(
                f"/playlists/{playlist_id}/tracks",
                params={"offset": offset, "limit": limit}
            )
            
            for item in data.get("items", []):
                track = item.get("track")
                if track and track.get("id"):  # Skip local files
                    tracks.append({
                        "id": track["id"],
                        "name": track["name"],
                        "artists": ", ".join(a["name"] for a in track.get("artists", [])),
                        "album": track.get("album", {}).get("name", ""),
                        "duration_ms": track.get("duration_ms", 0),
                        "isrc": track.get("external_ids", {}).get("isrc"),
                    })
            
            if not data.get("next"):
                break
            offset += limit
        
        return tracks


def get_spotify_api() -> Optional[SpotifyAPI]:
    """Get configured Spotify API client, or None if not configured."""
    config = load_config()
    client_id = config.get("spotify_client_id")
    client_secret = config.get("spotify_client_secret")
    
    if client_id and client_secret:
        return SpotifyAPI(client_id, client_secret)
    return None


def get_playlist_from_local_db(playlist_id: str) -> Optional[Dict]:
    """
    Get playlist from local spotify_clean_playlists.sqlite3.
    Returns None if not found or DB not configured.
    """
    import sqlite3
    from pathlib import Path
    
    config = load_config()
    db_path = config.get("playlists_db_path")
    
    if not db_path:
        return None
    
    path = Path(db_path)
    if not path.exists():
        return None
    
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get playlist info
    cursor.execute("""
        SELECT rowid, id, name, owner_id, owner_display_name, followers_total, tracks_total
        FROM playlists WHERE id = ?
    """, (playlist_id,))
    
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    
    playlist = dict(row)
    
    # Get tracks
    cursor.execute("""
        SELECT 
            pt.position,
            pt.track_rowid,
            pt.id_if_not_in_tracks_table,
            t.id as track_id,
            t.name as track_name,
            t.duration_ms
        FROM playlist_tracks pt
        LEFT JOIN tracks t ON pt.track_rowid = t.rowid
        WHERE pt.playlist_rowid = ?
        ORDER BY pt.position
    """, (playlist["rowid"],))
    
    # Note: This query assumes we have access to the main tracks table
    # If playlists DB is separate, we only get track_rowid or id_if_not_in_tracks_table
    tracks = []
    for track_row in cursor.fetchall():
        track_data = dict(track_row)
        track_id = track_data.get("track_id") or track_data.get("id_if_not_in_tracks_table")
        if track_id:
            tracks.append({
                "id": track_id,
                "position": track_data.get("position"),
                "name": track_data.get("track_name"),
                "duration_ms": track_data.get("duration_ms"),
            })
    
    playlist["tracks"] = tracks
    conn.close()
    
    return playlist


def get_playlist_track_ids_from_local_db(playlist_id: str) -> Optional[List[str]]:
    """
    Get just the track IDs from a playlist in local DB.
    More efficient when we only need IDs for matching.
    """
    import sqlite3
    from pathlib import Path
    
    config = load_config()
    db_path = config.get("playlists_db_path")
    
    if not db_path:
        return None
    
    path = Path(db_path)
    if not path.exists():
        return None
    
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get playlist rowid
    cursor.execute("SELECT rowid FROM playlists WHERE id = ?", (playlist_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    
    playlist_rowid = row["rowid"]
    
    # Get track IDs - need to get them from the main DB
    # The playlists DB only has track_rowid references
    cursor.execute("""
        SELECT track_rowid, id_if_not_in_tracks_table
        FROM playlist_tracks
        WHERE playlist_rowid = ?
        ORDER BY position
    """, (playlist_rowid,))
    
    # We need to resolve track_rowid to track_id using main DB
    track_refs = cursor.fetchall()
    conn.close()
    
    # For now, return the id_if_not_in_tracks_table if available
    # Full resolution requires joining with main DB
    track_ids = []
    for ref in track_refs:
        if ref["id_if_not_in_tracks_table"]:
            track_ids.append(ref["id_if_not_in_tracks_table"])
        # track_rowid needs to be resolved against main DB
    
    return track_ids if track_ids else None


def fetch_playlist(url: str) -> dict:
    """
    Fetch playlist info and tracks, trying local DB first, then API.
    
    Returns:
        dict with 'name', 'owner', 'total_tracks', 'tracks' (list of track dicts),
        and 'source' ('local_db' or 'api')
    
    Raises:
        ValueError: If URL is invalid
        FileNotFoundError: If no data source is available
        requests.RequestException: If API request fails
    """
    parsed = parse_spotify_url(url)
    if not parsed:
        raise ValueError(f"Invalid Spotify URL: {url}")
    
    item_type, item_id = parsed
    
    if item_type != "playlist":
        raise ValueError(f"URL is a {item_type}, not a playlist. Use 'musiccli album' for albums.")
    
    # Try local DB first
    local_data = get_playlist_from_local_db(item_id)
    if local_data:
        return {
            "id": item_id,
            "name": local_data.get("name", "Unknown"),
            "owner": local_data.get("owner_display_name") or local_data.get("owner_id", "Unknown"),
            "followers": local_data.get("followers_total", 0),
            "total_tracks": local_data.get("tracks_total", len(local_data.get("tracks", []))),
            "tracks": local_data.get("tracks", []),
            "source": "local_db"
        }
    
    # Try Spotify API
    api = get_spotify_api()
    if not api:
        raise FileNotFoundError(
            "Playlist not found in local database and Spotify API not configured.\n"
            "Either:\n"
            "  1. Download spotify_clean_playlists.sqlite3 and configure with:\n"
            "     musiccli setup --playlists-db-path /path/to/db\n"
            "  2. Configure Spotify API credentials:\n"
            "     musiccli setup --spotify-client-id <id> --spotify-client-secret <secret>"
        )
    
    # Fetch from API
    playlist_data = api.get_playlist(item_id)
    tracks = api.get_playlist_tracks(item_id)
    
    return {
        "id": item_id,
        "name": playlist_data.get("name", "Unknown"),
        "owner": playlist_data.get("owner", {}).get("display_name", "Unknown"),
        "followers": playlist_data.get("followers", {}).get("total", 0),
        "total_tracks": playlist_data.get("tracks", {}).get("total", len(tracks)),
        "tracks": tracks,
        "source": "api"
    }
