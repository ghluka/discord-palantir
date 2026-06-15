CREATE TABLE IF NOT EXISTS guilds (
    id BIGINT PRIMARY KEY,
    name TEXT,
    icon TEXT,
    icon_url TEXT,
    icon_cache_path TEXT,
    first_seen TIMESTAMP DEFAULT NOW(),
    last_scraped TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    username TEXT,
    discriminator TEXT,
    avatar TEXT,
    avatar_url TEXT,
    avatar_cache_path TEXT,
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP
);

CREATE TABLE IF NOT EXISTS guild_profile_history (
    id BIGSERIAL PRIMARY KEY,
    guild_id BIGINT,
    name TEXT,
    icon TEXT,
    icon_url TEXT,
    icon_cache_path TEXT,
    seen_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_guild_profile_history_guild
ON guild_profile_history (guild_id, seen_at DESC);

CREATE TABLE IF NOT EXISTS user_profile_history (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    username TEXT,
    discriminator TEXT,
    avatar TEXT,
    avatar_url TEXT,
    avatar_cache_path TEXT,
    seen_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_profile_history_user
ON user_profile_history (user_id, seen_at DESC);

CREATE TABLE IF NOT EXISTS guild_memberships (
    user_id BIGINT,
    guild_id BIGINT,
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP,
    PRIMARY KEY (user_id, guild_id)
);

CREATE INDEX IF NOT EXISTS idx_membership_user
ON guild_memberships (user_id);

CREATE TABLE IF NOT EXISTS channels (
    id BIGINT PRIMARY KEY,
    guild_id BIGINT,
    name TEXT,
    type INTEGER,
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_channels_guild
ON channels (guild_id);

CREATE TABLE IF NOT EXISTS messages (
    id BIGINT PRIMARY KEY,
    guild_id BIGINT,
    channel_id BIGINT,
    user_id BIGINT,
    created_at TIMESTAMP,
    content TEXT
);

CREATE INDEX IF NOT EXISTS idx_messages_user
ON messages (user_id);

CREATE INDEX IF NOT EXISTS idx_messages_channel
ON messages (channel_id);

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
);

CREATE INDEX IF NOT EXISTS idx_message_media_message
ON message_media (message_id);

CREATE TABLE IF NOT EXISTS channel_state (
    channel_id BIGINT PRIMARY KEY,
    last_message_id BIGINT
);
