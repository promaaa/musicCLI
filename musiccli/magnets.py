# musiccli/magnets.py
"""Magnet link generation for Anna's Archive Spotify torrents."""

import webbrowser
import urllib.parse

# Anna's Archive tracker
AA_TRACKER = "udp://tracker.opentrackr.org:1337/announce"

# Known Spotify torrent hashes from Anna's Archive
# These are the main torrents for the Spotify collection
SPOTIFY_TORRENTS = {
    "metadata": {
        "hash": "TBD",  # Will be filled with actual hash
        "name": "annas_archive_spotify_2025_07_metadata",
        "description": "Spotify metadata SQLite databases (~200GB)"
    },
    "audio_analysis": {
        "hash": "afc275bcf57137317e22e296a5ee20af8000444f",
        "name": "annas_archive_spotify_2025_07_audio_analysis",
        "description": "Spotify audio analysis data (~4TB)"
    },
    "coverart": {
        "hash": "5bccfd692a2ce67234b00c8865ab58e36b9b72d3",
        "name": "annas_archive_spotify_2025_07_coverart.tar",
        "description": "Album artwork"
    }
}


def build_magnet(torrent_hash: str, name: str) -> str:
    """Build a magnet link with Anna's Archive tracker."""
    dn = urllib.parse.quote(name)
    tracker = urllib.parse.quote(AA_TRACKER)
    return f"magnet:?xt=urn:btih:{torrent_hash}&dn={dn}&tr={tracker}"


def get_metadata_magnet() -> str:
    """Get magnet link for the Spotify metadata torrent."""
    info = SPOTIFY_TORRENTS["metadata"]
    return build_magnet(info["hash"], info["name"])


def get_coverart_magnet() -> str:
    """Get magnet link for the cover art torrent."""
    info = SPOTIFY_TORRENTS["coverart"]
    return build_magnet(info["hash"], info["name"])


def get_torrent_for_track(filename: str) -> dict:
    """
    Identify which AAC torrent contains a specific track file.
    
    The filename format from track_files table indicates the AAC container.
    Format: usually like "aac_spotify_XXXXXXX/file.ogg"
    
    Returns dict with torrent info or None if can't be determined.
    """
    if not filename:
        return None
    
    # The filename in track_files indicates the AAC container
    # We return info about where to find torrents
    parts = filename.split("/")
    if parts:
        container = parts[0]
        return {
            "container": container,
            "filename": filename,
            "torrents_url": "https://annas-archive.li/torrents#spotify",
            "note": "Music files are distributed in bulk AAC torrents organized by popularity"
        }
    
    return None


def open_magnet(magnet_url: str):
    """Open a magnet link in the default torrent client."""
    webbrowser.open(magnet_url)


def open_torrents_page():
    """Open the Anna's Archive torrents page for Spotify."""
    webbrowser.open("https://annas-archive.li/torrents#spotify")
