from datetime import datetime


class Models:

    @staticmethod
    def upsert_guild(db, guild):
        db.execute(
            """
            INSERT INTO guilds (id, name, last_scraped)
            VALUES (%s, %s, %s)
            ON CONFLICT (id)
            DO UPDATE SET
                name = EXCLUDED.name,
                last_scraped = EXCLUDED.last_scraped
        """,
            (int(guild["id"]), guild["name"], datetime.utcnow()),
        )

    @staticmethod
    def upsert_user(db, user):
        db.execute(
            """
            INSERT INTO users (id, username, discriminator, last_seen)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id)
            DO UPDATE SET
                username = EXCLUDED.username,
                discriminator = EXCLUDED.discriminator,
                last_seen = EXCLUDED.last_seen
        """,
            (
                int(user["id"]),
                user.get("username"),
                user.get("discriminator"),
                datetime.utcnow(),
            ),
        )

    @staticmethod
    def upsert_membership(db, user_id, guild_id):
        db.execute(
            """
            INSERT INTO guild_memberships (user_id, guild_id, last_seen)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, guild_id)
            DO UPDATE SET
                last_seen = EXCLUDED.last_seen
        """,
            (int(user_id), int(guild_id), datetime.utcnow()),
        )

    @staticmethod
    def insert_message(db, guild_id, channel_id, msg):
        db.execute(
            """
            INSERT INTO messages
            (id, guild_id, channel_id, user_id, created_at, content)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """,
            (
                int(msg["id"]),
                int(guild_id),
                int(channel_id),
                int(msg["author"]["id"]),
                msg["timestamp"],
                msg.get("content"),
            ),
        )

    @staticmethod
    def update_channel_state(db, channel_id, last_message_id):
        db.execute(
            """
            INSERT INTO channel_state (channel_id, last_message_id)
            VALUES (%s, %s)
            ON CONFLICT (channel_id)
            DO UPDATE SET last_message_id = EXCLUDED.last_message_id
        """,
            (channel_id, last_message_id),
        )
