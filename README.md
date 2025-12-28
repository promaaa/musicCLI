# MusicCLI

Download Spotify playlists from your terminal.

[![Version](https://img.shields.io/badge/version-0.2.0-blue)](https://github.com/promaaa/musicCLI)
[![Python](https://img.shields.io/badge/python-3.9+-green)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-purple)](LICENSE)

## What it does

Paste a Spotify playlist URL, and MusicCLI will:
- Fetch the track list from Spotify's API
- Check which tracks are in Anna's Archive
- Download missing ones from YouTube with proper metadata

You can also search for individual tracks and download them directly.

## Features

- Import playlists by URL
- Search tracks/artists/albums
- Download from YouTube with Spotify metadata
- Check availability in Anna's Archive
- Export to JSON/CSV
- Remote database (no 200GB download required)
- YouTube search caching

## Installation

You need Python 3.9+ and FFmpeg.

Install FFmpeg:
```bash
# macOS
brew install ffmpeg

# Linux
sudo apt install ffmpeg

# Windows
winget install ffmpeg
```

Install MusicCLI:
```bash
pip install musiccli
```

From source:
```bash
git clone https://github.com/promaaa/musicCLI
cd musicCLI
pip install -e .
```

## Quick Start

First, set up your Spotify API credentials (free, takes 2 minutes):

1. Create an app at [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Copy your Client ID and Secret
3. Run:
```bash
musiccli setup --spotify-client-id YOUR_ID --spotify-client-secret YOUR_SECRET
```

Now you're ready:

```bash
# Analyze a playlist
musiccli playlist https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M

# Download missing tracks
musiccli playlist https://open.spotify.com/playlist/... --download

# Download a single track
musiccli download "Bohemian Rhapsody"
```

## Commands

### Playlist import

```bash
musiccli playlist <url>
```

Options:
- `--all, -a` - Show all tracks (including those not in archive)
- `--download, -d` - Download missing tracks from YouTube  
- `--output, -o` - Where to save files (default: ./downloads)
- `--format, -f` - Audio format: mp3, m4a, opus (default: mp3)
- `--export, -e` - Export to JSON
- `--csv` - Export to CSV

Examples:
```bash
musiccli playlist <url> --all
musiccli playlist <url> --download --format m4a
musiccli playlist <url> --csv tracks.csv
```

### Single track download

```bash
musiccli download <query>
```

Examples:
```bash
musiccli download "Daft Punk Get Lucky"
musiccli download "Bohemian Rhapsody" --format m4a -o ~/Music
```

### Search

```bash
musiccli search <query>
musiccli search --type artist "queen"
musiccli search --type album "a night at the opera"
```

### Setup

```bash
# View current config
musiccli setup

# Set Spotify credentials
musiccli setup --spotify-client-id <id> --spotify-client-secret <secret>

# Use custom Turso database (optional)
musiccli setup --turso-url <url> --turso-token <token>

# Use local database (optional)
musiccli setup --db-path /path/to/spotify_clean.sqlite3
```

## Configuration

Config file: `~/.config/musiccli/config.toml`

```toml
spotify_client_id = "your_client_id"
spotify_client_secret = "your_client_secret"

# Optional: custom remote database
turso_url = "libsql://musiccli-db-xxx.turso.io"
turso_token = "your_token"

# Optional: local database files (200GB)
db_path = "/path/to/spotify_clean.sqlite3"
track_files_db_path = "/path/to/spotify_clean_track_files.sqlite3"
```

## How it works

1. You paste a Spotify playlist URL
2. MusicCLI fetches track metadata via Spotify API
3. Checks which tracks exist in the database (remote or local)
4. Downloads missing tracks from YouTube using yt-dlp
5. Embeds Spotify metadata in the audio files

The remote database is used by default - no setup needed. If you want faster queries or offline access, you can download the 200GB Anna's Archive metadata from [annas-archive.org/torrents#spotify](https://annas-archive.org/torrents#spotify).

## Caching

YouTube search results are cached in `~/.cache/musiccli/youtube_cache.json` (max 1000 entries). Delete the file to clear the cache.

## Tech

- Python 3.9+
- Typer (CLI)
- Rich (terminal UI)
- yt-dlp (YouTube downloads)
- libsql (Turso client)

## Contributing

PRs welcome.

```bash
git clone https://github.com/promaaa/musicCLI
cd musicCLI
pip install -e ".[all]"
```

## License

MIT

## Disclaimer

For personal use only. Respect copyright laws.
