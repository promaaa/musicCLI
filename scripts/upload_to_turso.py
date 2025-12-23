#!/usr/bin/env python3
"""
Script to upload the lightweight database to Turso.

Usage:
    export TURSO_DATABASE_URL="libsql://musiccli-db-xxx.turso.io"
    export TURSO_AUTH_TOKEN="your-token"
    python scripts/upload_to_turso.py musiccli_lite.sqlite3
"""

import os
import sys
import sqlite3
from pathlib import Path

try:
    import libsql_experimental as libsql
except ImportError:
    try:
        import libsql
    except ImportError:
        print("❌ libsql not installed. Run: pip install libsql-experimental")
        sys.exit(1)


def upload_to_turso(local_db_path: str):
    """Upload local SQLite database to Turso."""
    
    # Get Turso credentials
    turso_url = os.environ.get("TURSO_DATABASE_URL")
    turso_token = os.environ.get("TURSO_AUTH_TOKEN")
    
    if not turso_url:
        print("❌ TURSO_DATABASE_URL environment variable not set")
        print("   Get it with: turso db show <db-name> --url")
        sys.exit(1)
    
    if not turso_token:
        print("❌ TURSO_AUTH_TOKEN environment variable not set")
        print("   Get it with: turso db tokens create <db-name>")
        sys.exit(1)
    
    local_path = Path(local_db_path)
    if not local_path.exists():
        print(f"❌ Local database not found: {local_path}")
        sys.exit(1)
    
    print(f"📂 Local DB: {local_path}")
    print(f"🌐 Turso URL: {turso_url}")
    
    # Connect to local DB
    local_conn = sqlite3.connect(str(local_path))
    local_conn.row_factory = sqlite3.Row
    
    # Connect to Turso
    print("\n🔗 Connecting to Turso...")
    remote_conn = libsql.connect(database=turso_url, auth_token=turso_token)
    
    # Create schema
    print("🔨 Creating schema...")
    
    # Get schema from local DB
    schema_cursor = local_conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    
    for row in schema_cursor:
        if row['sql']:
            try:
                remote_conn.execute(row['sql'])
            except Exception as e:
                print(f"   ⚠️ Schema warning: {e}")
    
    remote_conn.commit()
    
    # Upload data table by table
    tables = ['tracks', 'artists', 'albums']
    
    for table in tables:
        print(f"\n📊 Uploading {table}...")
        
        # Get column names
        cursor = local_conn.execute(f"PRAGMA table_info({table})")
        columns = [row['name'] for row in cursor]
        
        # Count rows
        count_cursor = local_conn.execute(f"SELECT COUNT(*) FROM {table}")
        total = count_cursor.fetchone()[0]
        print(f"   Total rows: {total:,}")
        
        # Upload in batches
        batch_size = 1000
        offset = 0
        uploaded = 0
        
        placeholders = ",".join("?" * len(columns))
        insert_sql = f"INSERT OR REPLACE INTO {table} VALUES ({placeholders})"
        
        while True:
            cursor = local_conn.execute(
                f"SELECT * FROM {table} LIMIT {batch_size} OFFSET {offset}"
            )
            rows = cursor.fetchall()
            
            if not rows:
                break
            
            for row in rows:
                try:
                    remote_conn.execute(insert_sql, tuple(row))
                except Exception as e:
                    print(f"   ⚠️ Insert error: {e}")
            
            remote_conn.commit()
            uploaded += len(rows)
            offset += batch_size
            
            progress = (uploaded / total) * 100 if total > 0 else 100
            print(f"   Uploaded: {uploaded:,}/{total:,} ({progress:.1f}%)", end='\r')
        
        print(f"   ✅ Uploaded: {uploaded:,} rows")
    
    # Create indexes
    print("\n🔨 Creating indexes...")
    index_sqls = [
        "CREATE INDEX IF NOT EXISTS idx_tracks_name ON tracks(name)",
        "CREATE INDEX IF NOT EXISTS idx_tracks_isrc ON tracks(isrc)",
        "CREATE INDEX IF NOT EXISTS idx_artists_name ON artists(name)",
        "CREATE INDEX IF NOT EXISTS idx_albums_name ON albums(name)",
    ]
    
    for sql in index_sqls:
        try:
            remote_conn.execute(sql)
        except Exception as e:
            print(f"   ⚠️ Index warning: {e}")
    
    remote_conn.commit()
    
    local_conn.close()
    
    print("\n✅ Upload complete!")
    print(f"🌐 Database URL: {turso_url}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python upload_to_turso.py <local_db.sqlite3>")
        print("")
        print("Environment variables required:")
        print("  TURSO_DATABASE_URL  - Database URL from 'turso db show --url'")
        print("  TURSO_AUTH_TOKEN    - Token from 'turso db tokens create'")
        sys.exit(1)
    
    upload_to_turso(sys.argv[1])
