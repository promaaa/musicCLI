# MusicCLI 🎵

Terminal-first way to pull Spotify playlists with clean metadata.

[![Version](https://img.shields.io/badge/version-0.2.0-blue)](https://github.com/promaaa/musicCLI)
[![Python](https://img.shields.io/badge/python-3.9+-green)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-purple)](LICENSE)

## Highlights 

- Paste a Spotify playlist URL, get tracks with embedded metadata
- Fills gaps by pulling audio from YouTube via yt-dlp
- Checks availability against Anna's Archive (remote DB by default)
- Fast search (tracks, artists, albums) with caching
- Export results to JSON or CSV

## Install

Requires Python 3.9+ and FFmpeg.

```bash
# macOS
brew install ffmpeg

# Linux
sudo apt install ffmpeg

# Windows
winget install ffmpeg

# Install the CLI
pip install musiccli
```

From source:

```bash
git clone https://github.com/promaaa/musicCLI
cd musicCLI
pip install -e .
```

## Configure

Create a Spotify app (free) at https://developer.spotify.com/dashboard, then run:

```bash
musiccli setup --spotify-client-id YOUR_ID --spotify-client-secret YOUR_SECRET
```

Configuration file: `~/.config/musiccli/config.toml`

```toml
spotify_client_id = "your_client_id"
spotify_client_secret = "your_client_secret"

# Optional remote DB (default is provided)
turso_url = "libsql://musiccli-db-xxx.turso.io"
turso_token = "your_token"

# Optional local DB (≈200GB) for offline/faster lookups
db_path = "/path/to/spotify_clean.sqlite3"
track_files_db_path = "/path/to/spotify_clean_track_files.sqlite3"
```

## Use it 

```bash
# Analyze a playlist
musiccli playlist https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M

# Download missing tracks
musiccli playlist <url> --download

# Download one track
musiccli download "Bohemian Rhapsody"

# Search
musiccli search --type artist "queen"
```

Playlist options:
- `--download, -d` download missing tracks from YouTube
- `--all, -a` show all tracks, including missing
- `--output, -o` output directory (default: ./downloads)
- `--format, -f` audio format: mp3 | m4a | opus (default: mp3)
- `--export, -e` export results to JSON
- `--csv` export results to CSV

## How it works

1. Fetch playlist metadata from Spotify
2. Check track availability in the remote (or local) database
3. For missing tracks, search YouTube and download with yt-dlp
4. Write audio files with Spotify tags embedded

The hosted database is enabled by default—no 200GB download required. Power users can point to local Anna's Archive databases for offline or faster queries.

## Caching

YouTube search results cache: `~/.cache/musiccli/youtube_cache.json` (max 1000 entries). Delete the file to reset.

## Tech

- Python 3.9+
- Typer (CLI)
- Rich (terminal UI)
- yt-dlp (YouTube downloads)
- libsql (Turso client)

## Contributing

Pull requests are welcome.

```bash
git clone https://github.com/promaaa/musicCLI
cd musicCLI
pip install -e ".[all]"
```

## License

MIT

## Disclaimer

For personal use only. Respect copyright laws.
