from datetime import datetime

from psycopg.types.json import Json

try:
    from .media_cache import cache_remote_asset, guild_icon_url, user_avatar_url
except ImportError:
    from media_cache import cache_remote_asset, guild_icon_url, user_avatar_url


class Models:

    @staticmethod
    def upsert_guild(db, guild):
        icon_url = guild_icon_url(guild)
        icon_cache_path = cache_remote_asset("guilds", guild["id"], guild.get("icon"), icon_url)

        db.execute(
            """
            INSERT INTO guilds (id, name, icon, icon_url, icon_cache_path, last_scraped)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id)
            DO UPDATE SET
                name = EXCLUDED.name,
                icon = EXCLUDED.icon,
                icon_url = EXCLUDED.icon_url,
                icon_cache_path = EXCLUDED.icon_cache_path,
                last_scraped = EXCLUDED.last_scraped
        """,
            (
                int(guild["id"]),
                guild["name"],
                guild.get("icon"),
                icon_url,
                icon_cache_path,
                datetime.utcnow(),
            ),
        )
        Models.insert_guild_profile_history(db, guild, icon_url, icon_cache_path)

    @staticmethod
    def upsert_user(db, user):
        avatar_url = user_avatar_url(user)
        avatar_cache_path = cache_remote_asset(
            "users", user["id"], user.get("avatar"), avatar_url
        )

        db.execute(
            """
            INSERT INTO users
            (id, username, discriminator, avatar, avatar_url, avatar_cache_path, last_seen)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id)
            DO UPDATE SET
                username = EXCLUDED.username,
                discriminator = EXCLUDED.discriminator,
                avatar = EXCLUDED.avatar,
                avatar_url = EXCLUDED.avatar_url,
                avatar_cache_path = EXCLUDED.avatar_cache_path,
                last_seen = EXCLUDED.last_seen
        """,
            (
                int(user["id"]),
                user.get("username"),
                user.get("discriminator"),
                user.get("avatar"),
                avatar_url,
                avatar_cache_path,
                datetime.utcnow(),
            ),
        )
        Models.insert_user_profile_history(db, user, avatar_url, avatar_cache_path)

    @staticmethod
    def insert_guild_profile_history(db, guild, icon_url, icon_cache_path):
        latest = db.fetchone(
            """
            SELECT name, icon
            FROM guild_profile_history
            WHERE guild_id = %s
            ORDER BY seen_at DESC
            LIMIT 1
            """,
            (int(guild["id"]),),
        )

        if latest == (guild.get("name"), guild.get("icon")):
            return

        db.execute(
            """
            INSERT INTO guild_profile_history
            (guild_id, name, icon, icon_url, icon_cache_path, seen_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                int(guild["id"]),
                guild.get("name"),
                guild.get("icon"),
                icon_url,
                icon_cache_path,
                datetime.utcnow(),
            ),
        )

    @staticmethod
    def insert_user_profile_history(db, user, avatar_url, avatar_cache_path):
        latest = db.fetchone(
            """
            SELECT username, discriminator, avatar
            FROM user_profile_history
            WHERE user_id = %s
            ORDER BY seen_at DESC
            LIMIT 1
            """,
            (int(user["id"]),),
        )

        current = (user.get("username"), user.get("discriminator"), user.get("avatar"))
        if latest == current:
            return

        db.execute(
            """
            INSERT INTO user_profile_history
            (user_id, username, discriminator, avatar, avatar_url, avatar_cache_path, seen_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                int(user["id"]),
                user.get("username"),
                user.get("discriminator"),
                user.get("avatar"),
                avatar_url,
                avatar_cache_path,
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
    def upsert_channel(db, guild_id, channel):
        db.execute(
            """
            INSERT INTO channels (id, guild_id, name, type, last_seen)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id)
            DO UPDATE SET
                guild_id = EXCLUDED.guild_id,
                name = EXCLUDED.name,
                type = EXCLUDED.type,
                last_seen = EXCLUDED.last_seen
            """,
            (
                int(channel["id"]),
                int(guild_id),
                channel.get("name"),
                channel.get("type"),
                datetime.utcnow(),
            ),
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
        Models.insert_message_media(db, msg)

    @staticmethod
    def insert_message_media(db, msg):
        for index, media in enumerate(Models.extract_message_media(msg)):
            db.execute(
                """
                INSERT INTO message_media
                (
                    message_id,
                    media_index,
                    kind,
                    url,
                    proxy_url,
                    filename,
                    content_type,
                    size_bytes,
                    width,
                    height,
                    metadata
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (message_id, kind, url) DO UPDATE SET
                    media_index = EXCLUDED.media_index,
                    proxy_url = EXCLUDED.proxy_url,
                    filename = EXCLUDED.filename,
                    content_type = EXCLUDED.content_type,
                    size_bytes = EXCLUDED.size_bytes,
                    width = EXCLUDED.width,
                    height = EXCLUDED.height,
                    metadata = EXCLUDED.metadata
                """,
                (
                    int(msg["id"]),
                    index,
                    media.get("kind"),
                    media.get("url"),
                    media.get("proxy_url"),
                    media.get("filename"),
                    media.get("content_type"),
                    media.get("size"),
                    media.get("width"),
                    media.get("height"),
                    Json(media.get("metadata", {})),
                ),
            )

    @staticmethod
    def extract_message_media(msg):
        media = []

        for attachment in msg.get("attachments", []):
            if attachment.get("url"):
                media.append(
                    {
                        "kind": "attachment",
                        "url": attachment.get("url"),
                        "proxy_url": attachment.get("proxy_url"),
                        "filename": attachment.get("filename"),
                        "content_type": attachment.get("content_type"),
                        "size": attachment.get("size"),
                        "width": attachment.get("width"),
                        "height": attachment.get("height"),
                        "metadata": {"attachment_id": attachment.get("id")},
                    }
                )

        for embed_index, embed in enumerate(msg.get("embeds", [])):
            for field, kind in (
                ("image", "embed_image"),
                ("thumbnail", "embed_thumbnail"),
                ("video", "embed_video"),
            ):
                item = embed.get(field) or {}
                if item.get("url"):
                    media.append(
                        {
                            "kind": kind,
                            "url": item.get("url"),
                            "proxy_url": item.get("proxy_url"),
                            "width": item.get("width"),
                            "height": item.get("height"),
                            "metadata": {
                                "embed_index": embed_index,
                                "embed_type": embed.get("type"),
                            },
                        }
                    )

        for sticker in msg.get("sticker_items", []):
            sticker_url = Models.sticker_url(sticker)
            if sticker_url:
                media.append(
                    {
                        "kind": "sticker",
                        "url": sticker_url,
                        "filename": sticker.get("name"),
                        "metadata": {
                            "sticker_id": sticker.get("id"),
                            "format_type": sticker.get("format_type"),
                        },
                    }
                )

        return media

    @staticmethod
    def sticker_url(sticker):
        if not sticker.get("id"):
            return None

        extensions = {
            1: "png",
            2: "png",
            3: "json",
            4: "gif",
        }
        ext = extensions.get(sticker.get("format_type"))
        if not ext:
            return None

        return f"https://cdn.discordapp.com/stickers/{sticker['id']}.{ext}"

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
