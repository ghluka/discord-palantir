CREATE TABLE IF NOT EXISTS guilds (
    id BIGINT PRIMARY KEY,
    name TEXT,
    first_seen TIMESTAMP DEFAULT NOW(),
    last_scraped TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    username TEXT,
    discriminator TEXT,
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP
);

CREATE TABLE IF NOT EXISTS guild_memberships (
    user_id BIGINT,
    guild_id BIGINT,
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP,
    PRIMARY KEY (user_id, guild_id)
);

CREATE INDEX IF NOT EXISTS idx_membership_user
ON guild_memberships (user_id);

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

CREATE TABLE IF NOT EXISTS channel_state (
    channel_id BIGINT PRIMARY KEY,
    last_message_id BIGINT
);
