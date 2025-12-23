# musiccli/youtube.py
"""
YouTube fallback module for downloading tracks via yt-dlp.
Searches YouTube Music and downloads audio when tracks are not in Anna's Archive.
"""

import os
import re
from pathlib import Path
from typing import Optional, List, Dict, Callable

# yt-dlp is imported lazily to avoid startup penalty
_ydl_module = None


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


def build_search_query(track: Dict) -> str:
    """
    Build a search query from track metadata.
    Format: "Artist - Title" for best YouTube Music results.
    """
    artists = track.get("artists", "")
    if isinstance(artists, list):
        artists = ", ".join(a.get("name", a) if isinstance(a, dict) else a for a in artists)
    
    title = track.get("name", "")
    
    # Clean up the query
    query = f"{artists} - {title}".strip()
    
    # Remove common suffixes that hurt search
    query = re.sub(r'\s*\(.*?(remaster|remix|live|version|edit).*?\)', '', query, flags=re.IGNORECASE)
    
    return query


def search_youtube(
    query: str,
    limit: int = 1,
    music_only: bool = True
) -> List[Dict]:
    """
    Search YouTube (or YouTube Music) for tracks.
    
    Args:
        query: Search query (e.g., "Queen - Bohemian Rhapsody")
        limit: Number of results to return
        music_only: If True, prefer YouTube Music results
        
    Returns:
        List of track info dicts with id, title, url, duration, etc.
    """
    yt_dlp = _get_ydl()
    
    # Use ytsearch for YouTube Music (better for songs)
    search_prefix = "ytsearch" if not music_only else "ytsearch"
    search_url = f"{search_prefix}{limit}:{query}"
    
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
            
            # Filter out None entries
            return [
                {
                    'id': e.get('id'),
                    'title': e.get('title'),
                    'url': e.get('url') or f"https://www.youtube.com/watch?v={e.get('id')}",
                    'duration': e.get('duration'),
                    'channel': e.get('channel') or e.get('uploader'),
                    'view_count': e.get('view_count'),
                }
                for e in entries if e is not None
            ]
            
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
