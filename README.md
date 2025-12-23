<p align="center">
  <h1 align="center">🎵 MusicCLI</h1>
  <p align="center">
    <strong>Download Spotify playlists from your terminal</strong>
  </p>
  <p align="center">
    <a href="#features">Features</a> •
    <a href="#installation">Installation</a> •
    <a href="#quick-start">Quick Start</a> •
    <a href="#commands">Commands</a> •
    <a href="#configuration">Configuration</a>
  </p>
</p>

---

## What is MusicCLI?

MusicCLI is a command-line tool that lets you:
- 📋 **Import Spotify playlists** by URL
- 🔍 **Search** for tracks, artists, and albums
- ⬇️ **Download** tracks via YouTube (with metadata from Spotify)
- 📊 **Analyze** playlist availability in Anna's Archive

> **Note**: This tool searches YouTube for audio files - it doesn't directly download from Spotify.

---

## Features

| Feature | Description |
|---------|-------------|
| � **Playlist Import** | Paste a Spotify playlist URL, get all tracks |
| 🔍 **Search** | Search tracks, artists, albums by name |
| ⬇️ **YouTube Download** | Download audio from YouTube with Spotify metadata |
| 📊 **Archive Check** | See which tracks exist in Anna's Archive (optional) |
| 🎨 **Rich UI** | Beautiful terminal interface with colors and tables |

---

## Installation

### Prerequisites
- Python 3.9+ (3.10+ recommended)
- FFmpeg (for audio conversion)

```bash
# Install FFmpeg (macOS)
brew install ffmpeg

# Install FFmpeg (Ubuntu/Debian)
sudo apt install ffmpeg
```

### Install MusicCLI

```bash
pip install musiccli
```

Or from source:

```bash
git clone https://github.com/promaaa/musicCLI
cd musicCLI
pip install -e .
```

---

## Quick Start

### 1. Configure Spotify API (required for playlists)

Create a free Spotify app at [developer.spotify.com](https://developer.spotify.com/dashboard):

```bash
musiccli setup --spotify-client-id YOUR_ID --spotify-client-secret YOUR_SECRET
```

### 2. Download a playlist

```bash
# Analyze a playlist
musiccli playlist https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M

# Download missing tracks via YouTube
musiccli playlist https://open.spotify.com/playlist/... --download
```

### 3. Download a single track

```bash
musiccli download "Queen Bohemian Rhapsody"
```

---

## Commands

### `musiccli playlist <url>`

Import and analyze a Spotify playlist.

```bash
# Basic usage
musiccli playlist https://open.spotify.com/playlist/...

# Show all tracks (including missing)
musiccli playlist <url> --all

# Download tracks via YouTube
musiccli playlist <url> --download

# Export to JSON
musiccli playlist <url> --export playlist.json

# Options
--all, -a         Show all tracks including missing
--download, -d    Download tracks via YouTube  
--output, -o      Output directory (default: ./downloads)
--format, -f      Audio format: mp3, m4a, opus (default: mp3)
--export, -e      Export results to JSON file
```

### `musiccli download <query>`

Download a single track from YouTube.

```bash
musiccli download "Artist Name - Song Title"
musiccli download "Bohemian Rhapsody" --format m4a
```

### `musiccli search <query>`

Search for tracks, artists, or albums (requires Anna's Archive DB).

```bash
musiccli search "bohemian rhapsody"
musiccli search --type artist "queen"
musiccli search --type album "a night at the opera"
```

### `musiccli setup`

Configure API credentials and database paths.

```bash
musiccli setup  # Show current config

# Spotify API (required for playlist import)
musiccli setup --spotify-client-id <id> --spotify-client-secret <secret>

# Anna's Archive databases (optional, for search/metadata)
musiccli setup --db-path /path/to/spotify_clean.sqlite3
musiccli setup --files-db-path /path/to/spotify_clean_track_files.sqlite3
```

### `musiccli torrents`

Open Anna's Archive Spotify torrents page in browser.

---

## Configuration

Config is stored in `~/.config/musiccli/config.toml`:

```toml
# Spotify API credentials (required for playlist import)
spotify_client_id = "your_client_id"
spotify_client_secret = "your_client_secret"

# Anna's Archive databases (optional)
db_path = "/path/to/spotify_clean.sqlite3"
track_files_db_path = "/path/to/spotify_clean_track_files.sqlite3"
```

### Getting Spotify API Credentials

1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Copy the Client ID and Client Secret
4. Run: `musiccli setup --spotify-client-id <id> --spotify-client-secret <secret>`

---

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                     MusicCLI Workflow                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Spotify Playlist URL                                    │
│         ↓                                                   │
│  2. Fetch metadata via Spotify API                          │
│         ↓                                                   │
│  3. For each track:                                         │
│      ├─ Check Anna's Archive (if configured) → Torrent     │
│      └─ Search YouTube Music → Download via yt-dlp         │
│         ↓                                                   │
│  4. Audio files with Spotify metadata                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Anna's Archive Integration (Optional)

For advanced users, you can download Anna's Archive Spotify metadata (~200GB) for:
- Faster local search
- Checking file availability before download
- Accessing 256 million tracks metadata

Visit [annas-archive.li/torrents#spotify](https://annas-archive.li/torrents#spotify) to download.

---

## Tech Stack

- **Python** 3.9+
- **Typer** - CLI framework
- **Rich** - Terminal UI
- **yt-dlp** - YouTube download
- **Requests** - HTTP client
- **SQLite** - Local database (optional)

---

## Roadmap

- [ ] Hosted metadata API (no 200GB download needed)
- [ ] SoundCloud/Deezer fallback
- [ ] Playlist sync & update
- [ ] GUI version

---

## Contributing

Contributions welcome! Please open an issue or PR.

---

## License

MIT

---

## Disclaimer

This tool is for personal use only. Respect copyright laws in your jurisdiction.
