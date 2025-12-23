# musiccli/cli.py
"""Command-line interface for MusicCLI."""

import typer
from rich.prompt import Prompt
from rich.console import Console
from typing import Optional
from enum import Enum

from musiccli.config import load_config, set_config_value, CONFIG_PATH
from musiccli.db import (
    search_tracks,
    search_artists,
    search_albums,
    get_track_details,
    get_artist_details,
    get_album_details,
    get_tracks_by_ids,
    get_tracks_file_info_batch,
)
from musiccli.ui import (
    show_tracks,
    show_track_details,
    show_artists,
    show_artist_details,
    show_albums,
    show_album_details,
    show_torrent_info,
    show_error,
    show_success,
    show_info,
    show_playlist_header,
    show_playlist_tracks,
    show_playlist_summary,
    console,
)
from musiccli.magnets import (
    open_torrents_page,
)
from musiccli.spotify import (
    parse_spotify_url,
    fetch_playlist,
)

# -------------------------------------------------
# App + Console
# -------------------------------------------------

from musiccli import __version__


def version_callback(value: bool):
    if value:
        console.print(f"[bold]MusicCLI[/bold] version {__version__}")
        raise typer.Exit()


app = typer.Typer(
    help="🎵 MusicCLI — Download Spotify playlists from your terminal",
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", "-V", callback=version_callback, is_eager=True,
        help="Show version and exit"
    ),
):
    """MusicCLI - Download Spotify playlists from your terminal."""
    pass


class SearchType(str, Enum):
    track = "track"
    artist = "artist"
    album = "album"


# -------------------------------------------------
# Setup command
# -------------------------------------------------

@app.command()
def setup(
    db_path: Optional[str] = typer.Option(None, "--db-path", "-d", help="Path to spotify_clean.sqlite3"),
    track_files_db_path: Optional[str] = typer.Option(None, "--files-db-path", "-f", help="Path to spotify_clean_track_files.sqlite3"),
    playlists_db_path: Optional[str] = typer.Option(None, "--playlists-db-path", "-p", help="Path to spotify_clean_playlists.sqlite3"),
    spotify_client_id: Optional[str] = typer.Option(None, "--spotify-client-id", help="Spotify API client ID"),
    spotify_client_secret: Optional[str] = typer.Option(None, "--spotify-client-secret", help="Spotify API client secret"),
    turso_url: Optional[str] = typer.Option(None, "--turso-url", help="Turso database URL"),
    turso_token: Optional[str] = typer.Option(None, "--turso-token", help="Turso auth token"),
):
    """
    Configure MusicCLI with database paths and API credentials.
    """
    if db_path:
        set_config_value("db_path", db_path)
        show_success(f"Main database path set: {db_path}")
    
    if track_files_db_path:
        set_config_value("track_files_db_path", track_files_db_path)
        show_success(f"Track files database path set: {track_files_db_path}")
    
    if playlists_db_path:
        set_config_value("playlists_db_path", playlists_db_path)
        show_success(f"Playlists database path set: {playlists_db_path}")
    
    if spotify_client_id:
        set_config_value("spotify_client_id", spotify_client_id)
        show_success("Spotify client ID set")
    
    if spotify_client_secret:
        set_config_value("spotify_client_secret", spotify_client_secret)
        show_success("Spotify client secret set")
    
    if turso_url:
        set_config_value("turso_url", turso_url)
        show_success(f"Turso URL set: {turso_url}")
    
    if turso_token:
        set_config_value("turso_token", turso_token)
        show_success("Turso token set")
    
    # Show current config if no options provided
    all_opts = [db_path, track_files_db_path, playlists_db_path, spotify_client_id, spotify_client_secret, turso_url, turso_token]
    if not any(all_opts):
        config = load_config()
        console.print("\n[bold]Current Configuration[/bold]")
        console.print(f"Config file: {CONFIG_PATH}")
        console.print()
        console.print("[bold]Local Databases:[/bold]")
        console.print(f"  Main DB: {config.get('db_path') or '[not set - using remote]'}")
        console.print(f"  Track files DB: {config.get('track_files_db_path') or '[not set]'}")
        console.print(f"  Playlists DB: {config.get('playlists_db_path') or '[not set]'}")
        console.print()
        console.print("[bold]Remote Database (Turso):[/bold]")
        console.print(f"  URL: {config.get('turso_url') or '[using default public DB]'}")
        console.print(f"  Token: {'[configured]' if config.get('turso_token') else '[not needed for public]'}")
        console.print()
        console.print("[bold]Spotify API:[/bold]")
        console.print(f"  {'Configured ✓' if config.get('spotify_client_id') else 'Not configured'}")
        console.print()
        console.print("[dim]Note: Without local DB, MusicCLI uses the public Turso database automatically.[/dim]")


# -------------------------------------------------
# Search command
# -------------------------------------------------

@app.command()
def search(
    query: list[str] = typer.Argument(..., help="Search query"),
    search_type: SearchType = typer.Option(SearchType.track, "--type", "-t", help="Type to search for"),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of results"),
):
    """
    Search for tracks, artists, or albums.
    """
    search_query = " ".join(query)
    
    try:
        if search_type == SearchType.track:
            results = search_tracks(search_query, limit)
            if not results:
                show_error("No tracks found.")
                raise typer.Exit(code=1)
            show_tracks(results)
        
        elif search_type == SearchType.artist:
            results = search_artists(search_query, limit)
            if not results:
                show_error("No artists found.")
                raise typer.Exit(code=1)
            show_artists(results)
        
        elif search_type == SearchType.album:
            results = search_albums(search_query, limit)
            if not results:
                show_error("No albums found.")
                raise typer.Exit(code=1)
            show_albums(results)
    
    except FileNotFoundError as e:
        show_error(str(e))
        raise typer.Exit(code=1)


# -------------------------------------------------
# Track info command
# -------------------------------------------------

@app.command()
def track(track_id: str = typer.Argument(..., help="Spotify track ID")):
    """
    View details for a specific track.
    """
    try:
        track_data = get_track_details(track_id)
        if not track_data:
            show_error(f"Track not found: {track_id}")
            raise typer.Exit(code=1)
        
        show_track_details(track_data)
        
        # Show torrent info if file available
        if track_data.get("file_info") and track_data["file_info"].get("status") == "success":
            console.print("\n[dim]This track is available in the Anna's Archive Spotify collection.[/dim]")
            console.print("[dim]Visit https://annas-archive.li/torrents#spotify to find bulk torrents.[/dim]")
            
            if typer.confirm("🌐 Open torrents page in browser?", default=False):
                open_torrents_page()
    
    except FileNotFoundError as e:
        show_error(str(e))
        raise typer.Exit(code=1)


# -------------------------------------------------
# Artist info command
# -------------------------------------------------

@app.command()
def artist(artist_id: str = typer.Argument(..., help="Spotify artist ID")):
    """
    View details for a specific artist and their albums.
    """
    try:
        artist_data = get_artist_details(artist_id)
        if not artist_data:
            show_error(f"Artist not found: {artist_id}")
            raise typer.Exit(code=1)
        
        show_artist_details(artist_data)
    
    except FileNotFoundError as e:
        show_error(str(e))
        raise typer.Exit(code=1)


# -------------------------------------------------
# Album info command
# -------------------------------------------------

@app.command()
def album(album_id: str = typer.Argument(..., help="Spotify album ID")):
    """
    View details for a specific album and its tracks.
    """
    try:
        album_data = get_album_details(album_id)
        if not album_data:
            show_error(f"Album not found: {album_id}")
            raise typer.Exit(code=1)
        
        show_album_details(album_data)
    
    except FileNotFoundError as e:
        show_error(str(e))
        raise typer.Exit(code=1)


# -------------------------------------------------
# Interactive command
# -------------------------------------------------

@app.command()
def interactive():
    """
    Interactive music browser (search → select → view details).
    """
    try:
        # Choose search type
        search_type = Prompt.ask(
            "🔍 What do you want to search for?",
            choices=["track", "artist", "album"],
            default="track"
        )
        
        query = Prompt.ask("🎵 Enter search query")
        
        if search_type == "track":
            results = search_tracks(query, limit=15)
            if not results:
                show_error("No tracks found.")
                raise typer.Exit()
            
            # Show results
            for idx, t in enumerate(results):
                artists = t.get("artists", "Unknown")
                console.print(
                    f"[cyan][{idx}][/cyan] "
                    f"{t['name']} — {artists} "
                    f"[dim]({t.get('popularity', 0)})[/dim]"
                )
            
            selection = Prompt.ask(
                "Select track index",
                choices=[str(i) for i in range(len(results))]
            )
            
            selected = results[int(selection)]
            track_data = get_track_details(selected["id"])
            show_track_details(track_data)
        
        elif search_type == "artist":
            results = search_artists(query, limit=15)
            if not results:
                show_error("No artists found.")
                raise typer.Exit()
            
            for idx, a in enumerate(results):
                console.print(
                    f"[cyan][{idx}][/cyan] "
                    f"{a['name']} "
                    f"[dim]({a.get('followers_total', 0)} followers)[/dim]"
                )
            
            selection = Prompt.ask(
                "Select artist index",
                choices=[str(i) for i in range(len(results))]
            )
            
            selected = results[int(selection)]
            artist_data = get_artist_details(selected["id"])
            show_artist_details(artist_data)
        
        elif search_type == "album":
            results = search_albums(query, limit=15)
            if not results:
                show_error("No albums found.")
                raise typer.Exit()
            
            for idx, al in enumerate(results):
                year = (al.get("release_date") or "")[:4]
                console.print(
                    f"[cyan][{idx}][/cyan] "
                    f"{al['name']} ({year}) "
                    f"[dim]{al.get('album_type', '')}[/dim]"
                )
            
            selection = Prompt.ask(
                "Select album index",
                choices=[str(i) for i in range(len(results))]
            )
            
            selected = results[int(selection)]
            album_data = get_album_details(selected["id"])
            show_album_details(album_data)
    
    except FileNotFoundError as e:
        show_error(str(e))
        raise typer.Exit()


# -------------------------------------------------
# Torrents command
# -------------------------------------------------

@app.command()
def torrents():
    """
    Open Anna's Archive Spotify torrents page.
    """
    show_info("Opening Anna's Archive torrents page...")
    open_torrents_page()
    show_success("Torrents page opened in browser.")


# -------------------------------------------------
# Playlist command
# -------------------------------------------------

@app.command()
def playlist(
    url: str = typer.Argument(..., help="Spotify playlist URL"),
    show_all: bool = typer.Option(False, "--all", "-a", help="Show all tracks including missing"),
    export: Optional[str] = typer.Option(None, "--export", "-e", help="Export results to JSON file"),
    csv_export: Optional[str] = typer.Option(None, "--csv", help="Export results to CSV file"),
    download: bool = typer.Option(False, "--download", "-d", help="Download tracks via YouTube"),
    output: str = typer.Option("./downloads", "--output", "-o", help="Output directory for downloads"),
    format: str = typer.Option("mp3", "--format", "-f", help="Audio format (mp3, m4a, opus)"),
    skip_existing: bool = typer.Option(True, "--skip-existing/--no-skip", help="Skip already downloaded tracks"),
    retries: int = typer.Option(3, "--retries", "-r", help="Number of retries for failed downloads"),
    workers: int = typer.Option(3, "--workers", "-w", help="Number of concurrent downloads"),
):
    """
    Import and analyze a Spotify playlist.
    
    Matches tracks with Anna's Archive database and shows availability.
    Use --download to download missing tracks via YouTube.
    """
    import json
    
    try:
        # Validate URL
        parsed = parse_spotify_url(url)
        if not parsed:
            show_error(f"Invalid Spotify URL: {url}")
            raise typer.Exit(code=1)
        
        item_type, item_id = parsed
        if item_type != "playlist":
            show_error(f"URL is a {item_type}, not a playlist.")
            show_info(f"Use 'musiccli {item_type} {item_id}' instead.")
            raise typer.Exit(code=1)
        
        # Fetch playlist
        show_info(f"Fetching playlist {item_id}...")
        playlist_data = fetch_playlist(url)
        
        # Show header
        show_playlist_header(playlist_data)
        
        # Get track IDs from playlist
        tracks = playlist_data.get("tracks", [])
        if not tracks:
            show_error("Playlist has no tracks.")
            raise typer.Exit(code=1)
        
        track_ids = [t["id"] for t in tracks if t.get("id")]
        
        # Match with local database
        show_info(f"Matching {len(track_ids)} tracks with Anna's Archive database...")
        
        # Get track metadata from main DB
        db_tracks = get_tracks_by_ids(track_ids)
        
        # Get file info
        file_infos = get_tracks_file_info_batch(track_ids)
        
        # Build results with status
        results = []
        stats = {"total": len(tracks), "available": 0, "missing": 0, "not_in_db": 0}
        
        for track in tracks:
            track_id = track.get("id")
            if not track_id:
                continue
            
            result = {
                "id": track_id,
                "name": track.get("name", "Unknown"),
                "artists": track.get("artists", "Unknown"),
                "duration_ms": track.get("duration_ms", 0),
            }
            
            # Check if in main DB
            if track_id in db_tracks:
                db_track = db_tracks[track_id]
                result["name"] = db_track.get("name", result["name"])
                result["artists"] = db_track.get("artists", result["artists"])
                result["duration_ms"] = db_track.get("duration_ms", result["duration_ms"])
                result["album_name"] = db_track.get("album_name")
                result["popularity"] = db_track.get("popularity")
                
                # Check file availability
                if track_id in file_infos:
                    fi = file_infos[track_id]
                    result["file_info"] = fi
                    if fi.get("status") == "success":
                        result["status"] = "available"
                        stats["available"] += 1
                    else:
                        result["status"] = "missing"
                        stats["missing"] += 1
                else:
                    # In DB but no file info - assume might be available
                    result["status"] = "available"
                    stats["available"] += 1
            else:
                result["status"] = "not_in_db"
                stats["not_in_db"] += 1
            
            results.append(result)
        
        # Show tracks
        show_playlist_tracks(results, show_all=show_all)
        
        # Show summary
        show_playlist_summary(stats)
        
        # Export if requested
        if export:
            export_data = {
                "playlist": {
                    "id": playlist_data.get("id"),
                    "name": playlist_data.get("name"),
                    "owner": playlist_data.get("owner"),
                    "total_tracks": playlist_data.get("total_tracks"),
                    "source": playlist_data.get("source"),
                },
                "stats": stats,
                "tracks": results,
            }
            with open(export, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            show_success(f"Exported to {export}")
        
        # CSV export if requested
        if csv_export:
            import csv
            with open(csv_export, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                # Header
                writer.writerow(["id", "name", "artists", "album", "duration_ms", "status"])
                # Data
                for r in results:
                    artists = r.get("artists", "")
                    if isinstance(artists, list):
                        artists = ", ".join(str(a) for a in artists)
                    writer.writerow([
                        r.get("id", ""),
                        r.get("name", ""),
                        artists,
                        r.get("album_name", ""),
                        r.get("duration_ms", ""),
                        r.get("status", ""),
                    ])
            show_success(f"Exported CSV to {csv_export}")
        
        # Download if requested
        if download:
            # Get tracks to download (missing from archive)
            tracks_to_download = [
                r for r in results 
                if r.get("status") in ("missing", "not_in_db")
            ]
            
            if not tracks_to_download:
                show_info("All tracks are available in Anna's Archive! No download needed.")
                show_info("Visit https://annas-archive.li/torrents#spotify to download the bulk torrents.")
            else:
                show_info(f"Downloading {len(tracks_to_download)} tracks via YouTube...")
                
                from musiccli.youtube import download_tracks_batch
                from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
                
                # Progress tracking
                downloaded = 0
                failed = 0
                skipped = 0
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    console=console,
                ) as progress:
                    task = progress.add_task("Downloading...", total=len(tracks_to_download))
                    
                    def progress_callback(track_name, status, info):
                        nonlocal downloaded, failed, skipped
                        if status == 'completed':
                            downloaded += 1
                            progress.update(task, advance=1, description=f"✅ {track_name[:30]}")
                        elif status == 'skipped':
                            skipped += 1
                            progress.update(task, advance=1, description=f"⏭️ {track_name[:30]}")
                        elif 'failed' in status or status == 'not_found':
                            failed += 1
                            progress.update(task, advance=1, description=f"❌ {track_name[:30]}")
                        elif status == 'downloading':
                            progress.update(task, description=f"⬇️ {track_name[:30]}")
                        elif status == 'searching':
                            progress.update(task, description=f"🔍 {track_name[:30]}")
                    
                    download_results = download_tracks_batch(
                        tracks=tracks_to_download,
                        output_dir=output,
                        format=format,
                        progress_callback=progress_callback,
                        skip_existing=skip_existing,
                        max_retries=retries,
                        max_workers=workers,
                    )
                
                console.print()
                show_success(f"Downloaded: {downloaded}/{len(tracks_to_download)}")
                if skipped > 0:
                    show_info(f"Skipped (already exists): {skipped}")
                if failed > 0:
                    show_error(f"Failed: {failed}")
                show_info(f"Files saved to: {output}")
    
    except FileNotFoundError as e:
        show_error(str(e))
        raise typer.Exit(code=1)
    except Exception as e:
        show_error(f"Error: {e}")
        raise typer.Exit(code=1)


# -------------------------------------------------
# Download command (standalone)
# -------------------------------------------------

@app.command()
def download(
    query: list[str] = typer.Argument(..., help="Track name or 'artist - title' to search"),
    output: str = typer.Option("./downloads", "--output", "-o", help="Output directory"),
    format: str = typer.Option("mp3", "--format", "-f", help="Audio format (mp3, m4a, opus)"),
):
    """
    Download a single track from YouTube by search query.
    
    Example: musiccli download "Queen Bohemian Rhapsody"
    """
    from musiccli.youtube import search_youtube, download_track
    
    search_query = " ".join(query)
    
    show_info(f"Searching YouTube for: {search_query}")
    
    results = search_youtube(search_query, limit=5)
    
    if not results:
        show_error("No results found on YouTube.")
        raise typer.Exit(code=1)
    
    # Show results
    console.print("\n[bold]Search Results:[/bold]")
    for idx, r in enumerate(results):
        duration = r.get('duration', 0)
        if duration:
            mins, secs = divmod(int(duration), 60)
            dur_str = f"{mins}:{secs:02d}"
        else:
            dur_str = "--:--"
        
        console.print(
            f"[cyan][{idx}][/cyan] "
            f"{r['title'][:50]} "
            f"[dim]({dur_str}) - {r.get('channel', 'Unknown')}[/dim]"
        )
    
    # Select
    selection = Prompt.ask(
        "Select track to download",
        choices=[str(i) for i in range(len(results))],
        default="0"
    )
    
    selected = results[int(selection)]
    
    show_info(f"Downloading: {selected['title']}")
    
    file_path = download_track(
        url=selected['url'],
        output_dir=output,
        format=format,
    )
    
    if file_path:
        show_success(f"Downloaded: {file_path}")
    else:
        show_error("Download failed.")
        raise typer.Exit(code=1)


# -------------------------------------------------
# Album download command
# -------------------------------------------------

@app.command(name="get-album")
def get_album(
    url: str = typer.Argument(..., help="Spotify album URL"),
    download: bool = typer.Option(False, "--download", "-d", help="Download all tracks"),
    output: str = typer.Option("./downloads", "--output", "-o", help="Output directory"),
    format: str = typer.Option("mp3", "--format", "-f", help="Audio format"),
):
    """
    Fetch a Spotify album and optionally download all tracks.
    
    Example: musiccli get-album https://open.spotify.com/album/...
    """
    from musiccli.spotify import parse_spotify_url, SpotifyClient
    from musiccli.youtube import download_tracks_batch
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    
    # Parse URL
    parsed = parse_spotify_url(url)
    if not parsed:
        show_error(f"Invalid Spotify URL: {url}")
        raise typer.Exit(code=1)
    
    item_type, item_id = parsed
    if item_type != "album":
        show_error(f"URL is a {item_type}, not an album.")
        raise typer.Exit(code=1)
    
    # Fetch album
    show_info(f"Fetching album {item_id}...")
    
    try:
        client = SpotifyClient()
        token = client._get_token()
        
        import requests
        resp = requests.get(
            f"https://api.spotify.com/v1/albums/{item_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        resp.raise_for_status()
        album_data = resp.json()
    except Exception as e:
        show_error(f"Failed to fetch album: {e}")
        raise typer.Exit(code=1)
    
    # Display album info
    album_name = album_data.get("name", "Unknown Album")
    artists = ", ".join(a["name"] for a in album_data.get("artists", []))
    total_tracks = album_data.get("total_tracks", 0)
    release_date = album_data.get("release_date", "Unknown")
    
    console.print(f"\n[bold]{album_name}[/bold]")
    console.print(f"[dim]{artists} • {release_date} • {total_tracks} tracks[/dim]\n")
    
    # Get tracks
    tracks = []
    for item in album_data.get("tracks", {}).get("items", []):
        track_artists = ", ".join(a["name"] for a in item.get("artists", []))
        tracks.append({
            "id": item.get("id"),
            "name": item.get("name"),
            "artists": track_artists,
            "album_name": album_name,
            "duration_ms": item.get("duration_ms"),
        })
    
    # Show tracks
    for i, t in enumerate(tracks, 1):
        duration = t.get("duration_ms", 0) // 1000
        mins, secs = divmod(duration, 60)
        console.print(f"  {i:2}. {t['name'][:45]:45} [dim]{mins}:{secs:02d}[/dim]")
    
    console.print()
    
    if not download:
        show_info(f"Use --download to download all {len(tracks)} tracks.")
        return
    
    # Download
    show_info(f"Downloading {len(tracks)} tracks...")
    
    downloaded = 0
    failed = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("Downloading...", total=len(tracks))
        
        def progress_cb(name, status, info):
            nonlocal downloaded, failed
            if status == 'completed':
                downloaded += 1
                progress.update(task, advance=1, description=f"✅ {name[:30]}")
            elif 'failed' in status or status == 'not_found':
                failed += 1
                progress.update(task, advance=1, description=f"❌ {name[:30]}")
            elif status == 'skipped':
                progress.update(task, advance=1, description=f"⏭️ {name[:30]}")
        
        download_tracks_batch(
            tracks=tracks,
            output_dir=output,
            format=format,
            progress_callback=progress_cb,
        )
    
    console.print()
    show_success(f"Downloaded: {downloaded}/{len(tracks)}")
    if failed > 0:
        show_error(f"Failed: {failed}")
    show_info(f"Files saved to: {output}")


# -------------------------------------------------
# Stats command
# -------------------------------------------------

@app.command()
def stats():
    """
    Show MusicCLI statistics and cache information.
    """
    import json
    from pathlib import Path
    
    cache_file = Path.home() / ".cache" / "musiccli" / "youtube_cache.json"
    config_file = Path.home() / ".config" / "musiccli" / "config.toml"
    
    console.print("\n[bold]📊 MusicCLI Stats[/bold]\n")
    
    # Cache info
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                cache = json.load(f)
            cache_size = cache_file.stat().st_size / 1024
            console.print(f"[bold]YouTube Cache:[/bold]")
            console.print(f"  Entries: {len(cache)}")
            console.print(f"  Size: {cache_size:.1f} KB")
            console.print(f"  Path: {cache_file}")
        except Exception:
            console.print("  Cache: [dim]Error reading[/dim]")
    else:
        console.print("  Cache: [dim]Not created yet[/dim]")
    
    console.print()
    
    # Config info
    console.print("[bold]Configuration:[/bold]")
    if config_file.exists():
        config = load_config()
        console.print(f"  Spotify API: {'✅ Configured' if config.get('spotify_client_id') else '❌ Not set'}")
        console.print(f"  Local DB: {'✅ ' + config.get('db_path', '')[:30] if config.get('db_path') else '❌ Using remote'}")
        console.print(f"  Turso: {'✅ Custom' if config.get('turso_url') else '🌐 Public DB'}")
    else:
        console.print("  [dim]No config file[/dim]")
    
    console.print()
