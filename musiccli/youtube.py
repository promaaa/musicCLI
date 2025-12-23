# musiccli/youtube.py
"""
YouTube fallback module for downloading tracks via yt-dlp.
Searches YouTube Music and downloads audio when tracks are not in Anna's Archive.
"""

import os
import re
import json
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Callable

# yt-dlp is imported lazily to avoid startup penalty
_ydl_module = None

# Simple in-memory cache for YouTube searches
_search_cache: Dict[str, List[Dict]] = {}
_CACHE_FILE = Path.home() / ".cache" / "musiccli" / "youtube_cache.json"


def _get_ydl():
    """Lazy import of yt-dlp."""
    global _ydl_module
    if _ydl_module is None:
        try:
            import yt_dlp
            _ydl_module = yt_dlp
        except ImportError:
            raise ImportError(
                "yt-dlp is required for YouTube fallback. "
                "Install with: pip install yt-dlp"
            )
    return _ydl_module


def _load_cache() -> Dict[str, List[Dict]]:
    """Load search cache from disk."""
    global _search_cache
    if _search_cache:
        return _search_cache
    
    try:
        if _CACHE_FILE.exists():
            with open(_CACHE_FILE, 'r', encoding='utf-8') as f:
                _search_cache = json.load(f)
    except Exception:
        _search_cache = {}
    
    return _search_cache


def _save_cache():
    """Save search cache to disk."""
    try:
        _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_CACHE_FILE, 'w', encoding='utf-8') as f:
            # Keep only last 1000 entries
            cache_to_save = dict(list(_search_cache.items())[-1000:])
            json.dump(cache_to_save, f)
    except Exception:
        pass


def _cache_key(query: str) -> str:
    """Generate cache key for a query."""
    return hashlib.md5(query.lower().encode()).hexdigest()


def build_search_query(track: Dict) -> str:
    """
    Build a search query from track metadata.
    Format: "Artist - Title" for best YouTube Music results.
    """
    artists = track.get("artists", "")
    if isinstance(artists, list):
        # Take first artist for cleaner search
        if artists:
            first_artist = artists[0]
            artists = first_artist.get("name", first_artist) if isinstance(first_artist, dict) else first_artist
        else:
            artists = ""
    
    title = track.get("name", "")
    
    # Clean up the query
    query = f"{artists} {title}".strip()
    
    # Remove common suffixes that hurt search
    query = re.sub(r'\s*[-–]\s*(Remaster(ed)?|Remix|Live|Version|Edit|Original|Mono|Stereo).*$', '', query, flags=re.IGNORECASE)
    query = re.sub(r'\s*\(.*?(remaster|remix|live|version|edit|feat\.|ft\.|with).*?\)', '', query, flags=re.IGNORECASE)
    query = re.sub(r'\s*\[.*?\]', '', query)  # Remove [anything]
    
    return query.strip()


def search_youtube(
    query: str,
    limit: int = 1,
    music_only: bool = True,
    use_cache: bool = True
) -> List[Dict]:
    """
    Search YouTube (or YouTube Music) for tracks.
    
    Args:
        query: Search query (e.g., "Queen Bohemian Rhapsody")
        limit: Number of results to return
        music_only: If True, filter for music content
        use_cache: If True, use cached results
        
    Returns:
        List of track info dicts with id, title, url, duration, etc.
    """
    # Check cache first
    cache = _load_cache()
    key = _cache_key(query)
    
    if use_cache and key in cache:
        cached = cache[key]
        return cached[:limit]
    
    yt_dlp = _get_ydl()
    
    # Use ytsearch for YouTube (more reliable than ytmsearch)
    # Adding "audio" to query helps find music
    search_query = f"{query} audio" if music_only else query
    search_url = f"ytsearch{limit + 5}:{search_query}"  # Get extra results for filtering
    
    opts = {
        'format': 'bestaudio/best',
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            result = ydl.extract_info(search_url, download=False)
            
            if not result:
                return []
            
            entries = result.get('entries', [])
            if not entries:
                return []
            
            # Filter and format results
            results = []
            for e in entries:
                if e is None:
                    continue
                
                # Skip very long videos (likely not music)
                duration = e.get('duration') or 0
                if duration > 900:  # > 15 minutes
                    continue
                
                results.append({
                    'id': e.get('id'),
                    'title': e.get('title'),
                    'url': e.get('url') or f"https://www.youtube.com/watch?v={e.get('id')}",
                    'duration': duration,
                    'channel': e.get('channel') or e.get('uploader'),
                    'view_count': e.get('view_count'),
                })
                
                if len(results) >= limit + 3:
                    break
            
            # Cache results
            if results:
                _search_cache[key] = results
                _save_cache()
            
            return results[:limit]
            
    except Exception as e:
        print(f"YouTube search error: {e}")
        return []


def download_track(
    url: str,
    output_dir: str = "./downloads",
    filename_template: Optional[str] = None,
    format: str = "mp3",
    quality: str = "320",
    metadata: Optional[Dict] = None,
    progress_callback: Optional[Callable] = None,
) -> Optional[str]:
    """
    Download a track from YouTube.
    
    Args:
        url: YouTube video URL
        output_dir: Directory to save the file
        filename_template: Output filename template (without extension)
        format: Audio format (mp3, m4a, opus, etc.)
        quality: Audio quality (320, 256, 192, etc.)
        metadata: Optional metadata to embed (title, artist, album, etc.)
        progress_callback: Optional callback for progress updates
        
    Returns:
        Path to downloaded file, or None if failed
    """
    yt_dlp = _get_ydl()
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Default filename template
    if not filename_template:
        filename_template = "%(title)s"
    
    outtmpl = os.path.join(output_dir, f"{filename_template}.%(ext)s")
    
    # Post-processors for audio extraction and metadata
    postprocessors = []
    
    # Extract audio
    if format in ('mp3', 'm4a', 'opus', 'flac', 'wav'):
        postprocessors.append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': format,
            'preferredquality': quality,
        })
    
    # Add metadata if provided
    if metadata:
        postprocessors.append({
            'key': 'FFmpegMetadata',
            'add_metadata': True,
        })
    
    opts = {
        'format': 'bestaudio/best',
        'outtmpl': outtmpl,
        'postprocessors': postprocessors,
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': False,
        'noplaylist': True,
    }
    
    # Add progress hook if callback provided
    if progress_callback:
        def progress_hook(d):
            if d['status'] == 'downloading':
                progress_callback(d.get('_percent_str', '0%'), 'downloading')
            elif d['status'] == 'finished':
                progress_callback('100%', 'finished')
        
        opts['progress_hooks'] = [progress_hook]
    
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            if not info:
                return None
            
            # Get the final filename
            # yt-dlp may change the extension after post-processing
            expected_file = ydl.prepare_filename(info)
            
            # Replace extension with target format
            base = os.path.splitext(expected_file)[0]
            final_file = f"{base}.{format}"
            
            if os.path.exists(final_file):
                return final_file
            
            # Try finding the file with original extension
            if os.path.exists(expected_file):
                return expected_file
                
            return None
            
    except Exception as e:
        print(f"Download error: {e}")
        return None


def download_tracks_batch(
    tracks: List[Dict],
    output_dir: str = "./downloads",
    format: str = "mp3",
    quality: str = "320",
    progress_callback: Optional[Callable] = None,
) -> Dict[str, str]:
    """
    Download multiple tracks from YouTube.
    
    Args:
        tracks: List of track dicts with 'name', 'artists', optionally 'youtube_url'
        output_dir: Directory to save files
        format: Audio format
        quality: Audio quality
        progress_callback: Callback(track_name, status, progress) for updates
        
    Returns:
        Dict mapping track_id -> downloaded file path (or None if failed)
    """
    results = {}
    
    for i, track in enumerate(tracks):
        track_id = track.get('id', str(i))
        track_name = track.get('name', 'Unknown')
        artists = track.get('artists', 'Unknown Artist')
        
        if progress_callback:
            progress_callback(track_name, 'searching', f"{i+1}/{len(tracks)}")
        
        # Search if no URL provided
        url = track.get('youtube_url')
        if not url:
            query = build_search_query(track)
            search_results = search_youtube(query, limit=1)
            
            if not search_results:
                if progress_callback:
                    progress_callback(track_name, 'not_found', None)
                results[track_id] = None
                continue
            
            url = search_results[0]['url']
        
        # Build filename
        if isinstance(artists, list):
            artist_str = ", ".join(artists)
        else:
            artist_str = str(artists)
        
        # Sanitize filename
        safe_name = re.sub(r'[<>:"/\\|?*]', '', f"{artist_str} - {track_name}")
        
        if progress_callback:
            progress_callback(track_name, 'downloading', '0%')
        
        # Download
        file_path = download_track(
            url=url,
            output_dir=output_dir,
            filename_template=safe_name,
            format=format,
            quality=quality,
            metadata={
                'title': track_name,
                'artist': artist_str,
                'album': track.get('album_name', ''),
            }
        )
        
        results[track_id] = file_path
        
        if progress_callback:
            status = 'completed' if file_path else 'failed'
            progress_callback(track_name, status, file_path)
    
    return results
