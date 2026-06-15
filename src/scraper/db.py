import os
import sys
from pathlib import Path

import psycopg

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_URL


class Database:
    def __init__(self, ensure_schema=True):
        self.conn = psycopg.connect(DATABASE_URL)
        self.conn.autocommit = True
        if ensure_schema:
            self.ensure_schema()

    def execute(self, query, params=None):
        with self.conn.cursor() as cur:
            cur.execute(query, params)

    def fetchone(self, query, params=None):
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()

    def fetchall(self, query, params=None):
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()

    def close(self):
        self.conn.close()

    def ensure_schema(self):
        schema_path = Path(__file__).resolve().parents[1] / "schema.sql"
        if schema_path.exists():
            with self.conn.cursor() as cur:
                cur.execute(schema_path.read_text())

        migrations = [
            "ALTER TABLE guilds ADD COLUMN IF NOT EXISTS icon TEXT",
            "ALTER TABLE guilds ADD COLUMN IF NOT EXISTS icon_url TEXT",
            "ALTER TABLE guilds ADD COLUMN IF NOT EXISTS icon_cache_path TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_cache_path TEXT",
            """
            CREATE TABLE IF NOT EXISTS guild_profile_history (
                id BIGSERIAL PRIMARY KEY,
                guild_id BIGINT,
                name TEXT,
                icon TEXT,
                icon_url TEXT,
                icon_cache_path TEXT,
                seen_at TIMESTAMP DEFAULT NOW()
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_guild_profile_history_guild
            ON guild_profile_history (guild_id, seen_at DESC)
            """,
            """
            CREATE TABLE IF NOT EXISTS user_profile_history (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT,
                username TEXT,
                discriminator TEXT,
                avatar TEXT,
                avatar_url TEXT,
                avatar_cache_path TEXT,
                seen_at TIMESTAMP DEFAULT NOW()
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_user_profile_history_user
            ON user_profile_history (user_id, seen_at DESC)
            """,
            """
            CREATE TABLE IF NOT EXISTS channels (
                id BIGINT PRIMARY KEY,
                guild_id BIGINT,
                name TEXT,
                type INTEGER,
                first_seen TIMESTAMP DEFAULT NOW(),
                last_seen TIMESTAMP
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_channels_guild
            ON channels (guild_id)
            """,
            """
            CREATE TABLE IF NOT EXISTS message_media (
                id BIGSERIAL PRIMARY KEY,
                message_id BIGINT,
                media_index INTEGER,
                kind TEXT,
                url TEXT,
                proxy_url TEXT,
                filename TEXT,
                content_type TEXT,
                size_bytes BIGINT,
                width INTEGER,
                height INTEGER,
                metadata JSONB,
                UNIQUE (message_id, kind, url)
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_message_media_message
            ON message_media (message_id)
            """,
        ]

        with self.conn.cursor() as cur:
            for migration in migrations:
                cur.execute(migration)
