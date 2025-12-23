<p align="center">
  <h1 align="center">🎵 MusicCLI</h1>
  <p align="center">
    <strong>Download Spotify playlists from your terminal</strong>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/version-0.2.0-blue" alt="Version">
    <img src="https://img.shields.io/badge/python-3.9+-green" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-purple" alt="License">
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
- ⬇️ **Download** tracks via YouTube (with Spotify metadata)
- 📊 **Analyze** playlist availability in Anna's Archive

> **How it works**: MusicCLI fetches playlist metadata from Spotify, then downloads the audio from YouTube using yt-dlp.

---

## Features

| Feature | Description |
|---------|-------------|
| 🔗 **Playlist Import** | Paste a Spotify playlist URL, get all tracks |
| 🔍 **Search** | Search tracks, artists, albums by name |
| ⬇️ **YouTube Download** | Download audio from YouTube with Spotify metadata |
| 📊 **Archive Check** | See which tracks exist in Anna's Archive |
| 💾 **Smart Caching** | Caches YouTube searches for faster repeat downloads |
| 📤 **Export** | Export playlists to JSON or CSV |
| 🌐 **Remote DB** | Uses hosted database (no 200GB download needed) |

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

# Install FFmpeg (Windows)
winget install ffmpeg
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

# Optional: Install remote database support
pip install -e ".[remote]"
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

# Export to CSV
musiccli playlist https://open.spotify.com/playlist/... --csv tracks.csv
```

### 3. Download a single track

```bash
musiccli download "Queen Bohemian Rhapsody"
```

### 4. Check version

```bash
musiccli --version
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

# Export to CSV
musiccli playlist <url> --csv playlist.csv

# Options
--all, -a         Show all tracks including missing
--download, -d    Download tracks via YouTube  
--output, -o      Output directory (default: ./downloads)
--format, -f      Audio format: mp3, m4a, opus (default: mp3)
--export, -e      Export results to JSON file
--csv             Export results to CSV file
```

### `musiccli download <query>`

Download a single track from YouTube.

```bash
musiccli download "Artist Name Song Title"
musiccli download "Bohemian Rhapsody" --format m4a
musiccli download "Daft Punk Get Lucky" -o ~/Music
```

### `musiccli search <query>`

Search for tracks, artists, or albums.

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

# Turso remote database (optional)
musiccli setup --turso-url <url> --turso-token <token>

# Local Anna's Archive databases (optional, for power users)
musiccli setup --db-path /path/to/spotify_clean.sqlite3
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

# Remote database (optional - uses public DB by default)
turso_url = "libsql://musiccli-db-xxx.turso.io"
turso_token = "your_token"

# Local databases (optional - for power users)
db_path = "/path/to/spotify_clean.sqlite3"
track_files_db_path = "/path/to/spotify_clean_track_files.sqlite3"
```

### Getting Spotify API Credentials

1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Create a new app (any name, any description)
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
│  3. Check track availability in database                    │
│      ├─ Remote Turso DB (default, no setup needed)         │
│      └─ Local Anna's Archive DB (optional, 200GB)          │
│         ↓                                                   │
│  4. For missing tracks:                                     │
│      └─ Search YouTube → Download via yt-dlp               │
│         ↓                                                   │
│  5. Audio files with Spotify metadata                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Database Options

### Option 1: Remote Database (Default)

By default, MusicCLI uses a hosted Turso database. **No configuration needed!**

- ✅ Works out of the box
- ✅ No large downloads
- ✅ Always up to date

### Option 2: Local Database (Power Users)

For offline use or faster queries, download Anna's Archive metadata:

1. Download from [annas-archive.org/torrents#spotify](https://annas-archive.org/torrents#spotify)
2. Get `annas_archive_spotify_2025_07_metadata.torrent` (~200GB)
3. Configure: `musiccli setup --db-path /path/to/spotify_clean.sqlite3`

---

## Caching

MusicCLI caches YouTube search results to speed up repeat downloads:

- Cache location: `~/.cache/musiccli/youtube_cache.json`
- Max entries: 1000 searches
- Clear cache: Delete the file

---

## Tech Stack

- **Python** 3.9+
- **Typer** - CLI framework
- **Rich** - Terminal UI
- **yt-dlp** - YouTube download
- **libsql** - Turso database client
- **Requests** - HTTP client

---

## Contributing

Contributions welcome! Please open an issue or PR.

```bash
# Development setup
git clone https://github.com/promaaa/musicCLI
cd musicCLI
pip install -e ".[all]"
```

---

## License

MIT

---

## Disclaimer

This tool is for personal use only. Respect copyright laws in your jurisdiction.
