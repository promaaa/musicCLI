#!/usr/bin/env python3
"""
Script to create a lightweight version of Anna's Archive Spotify database.
Extracts essential metadata for Turso hosting (~500MB vs 200GB original).

Usage:
    python scripts/create_turso_db.py /path/to/spotify_clean.sqlite3 output.sqlite3
"""

import sqlite3
import sys
from pathlib import Path


def create_lightweight_db(source_path: str, output_path: str):
    """
    Extract essential track/artist/album metadata from the full Anna's Archive DB.
    """
    source = Path(source_path)
    output = Path(output_path)
    
    if not source.exists():
        print(f"❌ Source database not found: {source}")
        sys.exit(1)
    
    if output.exists():
        print(f"⚠️  Output file exists, will be overwritten: {output}")
        output.unlink()
    
    print(f"📂 Source: {source}")
    print(f"📂 Output: {output}")
    
    # Connect to source
    src_conn = sqlite3.connect(str(source))
    src_conn.row_factory = sqlite3.Row
    
    # Create output database
    dst_conn = sqlite3.connect(str(output))
    
    print("\n🔨 Creating schema...")
    
    # Create simplified schema
    dst_conn.executescript("""
        -- Tracks table (main)
        CREATE TABLE tracks (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            artists TEXT,
            album_name TEXT,
            album_id TEXT,
            duration_ms INTEGER,
            popularity INTEGER,
            isrc TEXT
        );
        
        -- Artists table
        CREATE TABLE artists (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            popularity INTEGER,
            followers_total INTEGER
        );
        
        -- Albums table
        CREATE TABLE albums (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            artists TEXT,
            album_type TEXT,
            release_date TEXT,
            popularity INTEGER,
            total_tracks INTEGER
        );
        
        -- Indexes for fast search
        CREATE INDEX idx_tracks_name ON tracks(name);
        CREATE INDEX idx_tracks_isrc ON tracks(isrc);
        CREATE INDEX idx_tracks_popularity ON tracks(popularity);
        CREATE INDEX idx_artists_name ON artists(name);
        CREATE INDEX idx_albums_name ON albums(name);
    """)
    
    print("📊 Extracting tracks...")
    
    # Extract tracks with joined artist/album names
    # Limit to most popular tracks to reduce size
    cursor = src_conn.execute("""
        SELECT 
            t.id,
            t.name,
            GROUP_CONCAT(ar.name, ', ') as artists,
            a.name as album_name,
            a.id as album_id,
            t.duration_ms,
            t.popularity,
            t.external_id_isrc as isrc
        FROM tracks t
        JOIN albums a ON t.album_rowid = a.rowid
        LEFT JOIN track_artists ta ON ta.track_rowid = t.rowid
        LEFT JOIN artists ar ON ta.artist_rowid = ar.rowid
        WHERE t.popularity >= 10  -- Only tracks with some popularity
        GROUP BY t.id
        ORDER BY t.popularity DESC
    """)
    
    # Batch insert
    batch_size = 10000
    count = 0
    batch = []
    
    for row in cursor:
        batch.append((
            row['id'], row['name'], row['artists'], row['album_name'],
            row['album_id'], row['duration_ms'], row['popularity'], row['isrc']
        ))
        
        if len(batch) >= batch_size:
            dst_conn.executemany(
                "INSERT INTO tracks VALUES (?,?,?,?,?,?,?,?)", batch
            )
            dst_conn.commit()
            count += len(batch)
            print(f"   Inserted {count:,} tracks...")
            batch = []
    
    if batch:
        dst_conn.executemany("INSERT INTO tracks VALUES (?,?,?,?,?,?,?,?)", batch)
        dst_conn.commit()
        count += len(batch)
    
    print(f"   ✅ Total tracks: {count:,}")
    
    print("📊 Extracting artists...")
    
    cursor = src_conn.execute("""
        SELECT id, name, popularity, followers_total
        FROM artists
        WHERE followers_total >= 100 OR popularity >= 10
    """)
    
    count = 0
    batch = []
    
    for row in cursor:
        batch.append((row['id'], row['name'], row['popularity'], row['followers_total']))
        
        if len(batch) >= batch_size:
            dst_conn.executemany("INSERT INTO artists VALUES (?,?,?,?)", batch)
            dst_conn.commit()
            count += len(batch)
            batch = []
    
    if batch:
        dst_conn.executemany("INSERT INTO artists VALUES (?,?,?,?)", batch)
        dst_conn.commit()
        count += len(batch)
    
    print(f"   ✅ Total artists: {count:,}")
    
    print("📊 Extracting albums...")
    
    cursor = src_conn.execute("""
        SELECT 
            al.id,
            al.name,
            GROUP_CONCAT(ar.name, ', ') as artists,
            al.album_type,
            al.release_date,
            al.popularity,
            al.total_tracks
        FROM albums al
        LEFT JOIN artist_albums aa ON aa.album_rowid = al.rowid
        LEFT JOIN artists ar ON aa.artist_rowid = ar.rowid
        WHERE al.popularity >= 10
        GROUP BY al.id
    """)
    
    count = 0
    batch = []
    
    for row in cursor:
        batch.append((
            row['id'], row['name'], row['artists'], row['album_type'],
            row['release_date'], row['popularity'], row['total_tracks']
        ))
        
        if len(batch) >= batch_size:
            dst_conn.executemany("INSERT INTO albums VALUES (?,?,?,?,?,?,?)", batch)
            dst_conn.commit()
            count += len(batch)
            batch = []
    
    if batch:
        dst_conn.executemany("INSERT INTO albums VALUES (?,?,?,?,?,?,?)", batch)
        dst_conn.commit()
        count += len(batch)
    
    print(f"   ✅ Total albums: {count:,}")
    
    # Cleanup
    print("\n🧹 Optimizing database...")
    dst_conn.execute("VACUUM")
    dst_conn.close()
    src_conn.close()
    
    # Report size
    output_size = output.stat().st_size / (1024 * 1024)
    print(f"\n✅ Done! Output size: {output_size:.1f} MB")
    print(f"📁 Saved to: {output}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python create_turso_db.py <source.sqlite3> <output.sqlite3>")
        sys.exit(1)
    
    create_lightweight_db(sys.argv[1], sys.argv[2])
