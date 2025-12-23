# musiccli/ui.py
"""Terminal UI components for MusicCLI using Rich."""

from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def format_duration(ms: int) -> str:
    """Format milliseconds as MM:SS."""
    if not ms:
        return "--:--"
    seconds = ms // 1000
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes}:{seconds:02d}"


def format_followers(count: int) -> str:
    """Format follower count with K/M suffix."""
    if not count:
        return "0"
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    if count >= 1_000:
        return f"{count / 1_000:.1f}K"
    return str(count)


def show_tracks(tracks: list[dict]):
    """Display a list of tracks in a table."""
    table = Table(title="🎵 Tracks")

    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="bold")
    table.add_column("Artist(s)")
    table.add_column("Album")
    table.add_column("Duration", justify="center")
    table.add_column("Pop", justify="center")

    for track in tracks:
        table.add_row(
            track["id"],
            track["name"][:40] + ("..." if len(track.get("name", "")) > 40 else ""),
            (track.get("artists") or "Unknown")[:30],
            (track.get("album_name") or "")[:25],
            format_duration(track.get("duration_ms")),
            str(track.get("popularity", 0)),
        )

    console.print(table)


def show_track_details(track: dict):
    """Display detailed track information in a panel."""
    artists = ", ".join([a["name"] for a in track.get("artists", [])]) or "Unknown"
    duration = format_duration(track.get("duration_ms"))
    
    text = (
        f"[bold]{track['name']}[/bold]\n\n"
        f"🎤 Artist(s): {artists}\n"
        f"💿 Album: {track.get('album_name', 'Unknown')}\n"
        f"📅 Release: {track.get('release_date', 'Unknown')}\n"
        f"⏱ Duration: {duration}\n"
        f"🔥 Popularity: {track.get('popularity', 0)}/100\n"
        f"🆔 ISRC: {track.get('isrc') or 'N/A'}\n"
        f"🔞 Explicit: {'Yes' if track.get('explicit') else 'No'}\n"
    )
    
    # File info if available
    if track.get("file_info"):
        fi = track["file_info"]
        status = fi.get("status", "unknown")
        if status == "success":
            text += f"\n✅ File Status: Available\n"
            if fi.get("filename"):
                text += f"📁 Filename: {fi['filename']}\n"
            if fi.get("reencoded_kbit_vbr"):
                text += f"🎚 Quality: {fi['reencoded_kbit_vbr']}kbit/s (re-encoded)\n"
            else:
                text += f"🎚 Quality: 160kbit/s OGG Vorbis (original)\n"
        else:
            text += f"\n⚠️ File Status: {status}\n"
    
    console.print(Panel(text, title="🎵 Track Details", expand=False))


def show_artists(artists: list[dict]):
    """Display a list of artists in a table."""
    table = Table(title="🎤 Artists")

    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="bold")
    table.add_column("Followers", justify="right")
    table.add_column("Pop", justify="center")

    for artist in artists:
        table.add_row(
            artist["id"],
            artist["name"],
            format_followers(artist.get("followers_total", 0)),
            str(artist.get("popularity", 0)),
        )

    console.print(table)


def show_artist_details(artist: dict):
    """Display detailed artist information."""
    genres = ", ".join(artist.get("genres", [])) or "Not classified"
    
    text = (
        f"[bold]{artist['name']}[/bold]\n\n"
        f"👥 Followers: {format_followers(artist.get('followers_total', 0))}\n"
        f"🔥 Popularity: {artist.get('popularity', 0)}/100\n"
        f"🎭 Genres: {genres}\n"
    )
    
    console.print(Panel(text, title="🎤 Artist Details", expand=False))
    
    # Show albums
    albums = artist.get("albums", [])
    if albums:
        show_albums(albums)


def show_albums(albums: list[dict]):
    """Display a list of albums in a table."""
    table = Table(title="💿 Albums")

    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="bold")
    table.add_column("Type")
    table.add_column("Year", justify="center")
    table.add_column("Artist(s)")
    table.add_column("Pop", justify="center")

    for album in albums:
        year = (album.get("release_date") or "")[:4]
        table.add_row(
            album["id"],
            album["name"][:35] + ("..." if len(album.get("name", "")) > 35 else ""),
            album.get("album_type", "album"),
            year,
            (album.get("artists") or "")[:25] if isinstance(album.get("artists"), str) else "",
            str(album.get("popularity", 0)),
        )

    console.print(table)


def show_album_details(album: dict):
    """Display detailed album information with track list."""
    artists = ", ".join([a["name"] for a in album.get("artists", [])]) or "Unknown"
    
    text = (
        f"[bold]{album['name']}[/bold]\n\n"
        f"🎤 Artist(s): {artists}\n"
        f"📅 Release: {album.get('release_date', 'Unknown')}\n"
        f"📀 Type: {album.get('album_type', 'album')}\n"
        f"🔥 Popularity: {album.get('popularity', 0)}/100\n"
        f"🏷 Label: {album.get('label') or 'Unknown'}\n"
        f"🆔 UPC: {album.get('upc') or 'N/A'}\n"
    )
    
    console.print(Panel(text, title="💿 Album Details", expand=False))
    
    # Show tracks
    tracks = album.get("tracks", [])
    if tracks:
        table = Table(title="📋 Tracklist")
        table.add_column("#", justify="right", style="dim")
        table.add_column("Title")
        table.add_column("Duration", justify="center")
        table.add_column("ID", style="cyan")
        
        for track in tracks:
            table.add_row(
                str(track.get("track_number", "")),
                track["name"],
                format_duration(track.get("duration_ms")),
                track["id"],
            )
        
        console.print(table)


def show_torrent_info(track: dict, magnet: str):
    """Display torrent information for a track."""
    text = (
        f"🎵 [bold]{track['name']}[/bold]\n\n"
        f"This track is part of the Anna's Archive Spotify collection.\n"
        f"The music files are distributed in bulk torrents (~300TB total).\n\n"
        f"🧲 [cyan]Magnet Link:[/cyan]\n"
        f"[dim]{magnet[:80]}...[/dim]\n"
    )
    
    console.print(Panel(text, title="🧲 Torrent Info", expand=False))


def show_error(message: str):
    """Display an error message."""
    console.print(f"[red]❌ {message}[/red]")


def show_success(message: str):
    """Display a success message."""
    console.print(f"[green]✅ {message}[/green]")


def show_info(message: str):
    """Display an info message."""
    console.print(f"[blue]ℹ️ {message}[/blue]")


def show_playlist_header(playlist: dict):
    """Display playlist header information."""
    text = (
        f"[bold]{playlist.get('name', 'Unknown Playlist')}[/bold]\n\n"
        f"👤 Owner: {playlist.get('owner', 'Unknown')}\n"
        f"📊 Total tracks: {playlist.get('total_tracks', 0)}\n"
        f"👥 Followers: {format_followers(playlist.get('followers', 0))}\n"
        f"📡 Source: {playlist.get('source', 'unknown')}\n"
    )
    
    console.print(Panel(text, title="🎵 Playlist", expand=False))


def show_playlist_tracks(tracks: list[dict], show_all: bool = False):
    """
    Display playlist tracks with their archive status.
    
    Each track dict should have:
    - name, artists, duration_ms (from playlist or DB)
    - status: 'available', 'missing', 'not_in_db'
    - file_info (optional): dict with filename, quality info
    """
    table = Table(title="📋 Tracks")
    
    table.add_column("#", justify="right", style="dim", width=4)
    table.add_column("Status", justify="center", width=6)
    table.add_column("Title", style="bold", max_width=35)
    table.add_column("Artist(s)", max_width=25)
    table.add_column("Duration", justify="center", width=7)
    
    for i, track in enumerate(tracks, 1):
        status = track.get("status", "unknown")
        
        if status == "available":
            status_icon = "[green]✅[/green]"
        elif status == "missing":
            status_icon = "[red]❌[/red]"
        elif status == "not_in_db":
            status_icon = "[yellow]❓[/yellow]"
        else:
            status_icon = "[dim]?[/dim]"
        
        # Skip missing tracks if not showing all
        if not show_all and status in ("missing", "not_in_db"):
            continue
        
        name = track.get("name", "Unknown")[:35]
        artists = (track.get("artists") or "Unknown")[:25]
        duration = format_duration(track.get("duration_ms", 0))
        
        table.add_row(
            str(i),
            status_icon,
            name,
            artists,
            duration,
        )
    
    console.print(table)


def show_playlist_summary(stats: dict):
    """
    Display playlist analysis summary.
    
    stats should contain:
    - total: total tracks
    - available: tracks available in archive
    - missing: tracks not in archive
    - not_in_db: tracks not found in metadata DB
    """
    total = stats.get("total", 0)
    available = stats.get("available", 0)
    missing = stats.get("missing", 0)
    not_in_db = stats.get("not_in_db", 0)
    
    if total > 0:
        pct = (available / total) * 100
    else:
        pct = 0
    
    console.print()
    console.print("━" * 50)
    console.print()
    
    if pct >= 90:
        color = "green"
    elif pct >= 70:
        color = "yellow"
    else:
        color = "red"
    
    console.print(f"[{color}]✅ Available in archive: {available}/{total} ({pct:.1f}%)[/{color}]")
    
    if missing > 0:
        console.print(f"[red]❌ Not available (file status): {missing}[/red]")
    
    if not_in_db > 0:
        console.print(f"[yellow]❓ Not in metadata DB: {not_in_db}[/yellow]")
    
    console.print()
    console.print("[dim]The available tracks are distributed across Anna's Archive Spotify torrents.[/dim]")
    console.print("[dim]Visit https://annas-archive.li/torrents#spotify to download.[/dim]")

