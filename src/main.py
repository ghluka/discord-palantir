from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from flask import Flask, abort, jsonify, request, send_from_directory

from config import MEDIA_CACHE_DIR
from scraper.db import Database

app = Flask(__name__, static_folder="static", static_url_path="/static")
db = Database()


@app.route("/", methods=["GET"])
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/cache/<path:filename>", methods=["GET"])
def cached_media(filename):
    return send_from_directory(Path(MEDIA_CACHE_DIR), filename)


@app.route("/api/summary", methods=["GET"])
def get_summary():
    user_count = db.fetchone("SELECT COUNT(*) FROM users")[0]
    guild_count = db.fetchone("SELECT COUNT(*) FROM guilds")[0]
    message_count = db.fetchone("SELECT COUNT(*) FROM messages")[0]
    media_count = db.fetchone("SELECT COUNT(*) FROM message_media")[0]

    return jsonify(
        {
            "users": user_count,
            "guilds": guild_count,
            "messages": message_count,
            "media": media_count,
        }
    )


@app.route("/users", methods=["GET"])
def search_users():
    query = request.args.get("q", "").strip()
    limit = min(request.args.get("limit", 25, type=int), 100)

    if query.isdigit():
        rows = db.fetchall(
            """
            SELECT id, username, discriminator, avatar_url, avatar_cache_path, first_seen, last_seen
            FROM users
            WHERE id = %s OR username ILIKE %s
            ORDER BY last_seen DESC NULLS LAST
            LIMIT %s
            """,
            (int(query), f"%{query}%", limit),
        )
    else:
        rows = db.fetchall(
            """
            SELECT id, username, discriminator, avatar_url, avatar_cache_path, first_seen, last_seen
            FROM users
            WHERE username ILIKE %s
            ORDER BY last_seen DESC NULLS LAST
            LIMIT %s
            """,
            (f"%{query}%", limit),
        )

    return jsonify([serialize_user_row(row) for row in rows])


@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = db.fetchone(
        """
        SELECT id, username, discriminator, avatar, avatar_url, avatar_cache_path, first_seen, last_seen
        FROM users
        WHERE id = %s
        """,
        (user_id,),
    )

    if not user:
        abort(404, description="User not found")

    return jsonify(
        {
            "id": snowflake(user[0]),
            "username": user[1],
            "discriminator": user[2],
            "avatar": user[3],
            "avatar_url": webp_url(user[4]),
            "avatar_cache_path": cache_path(user[5]),
            "avatar_cache_url": cache_url(user[5]),
            "default_avatar_url": default_avatar_url(user[0], user[2]),
            "display_avatar_url": display_avatar_url(user[0], user[2], user[4], user[5]),
            "first_seen": user[6],
            "last_seen": user[7],
        }
    )


@app.route("/users/<int:user_id>/history", methods=["GET"])
def get_user_history(user_id):
    history = db.fetchall(
        """
        SELECT username, discriminator, avatar, avatar_url, avatar_cache_path, seen_at
        FROM user_profile_history
        WHERE user_id = %s
        ORDER BY seen_at DESC
        """,
        (user_id,),
    )

    return jsonify(
        [
            {
                "username": row[0],
                "discriminator": row[1],
                "avatar": row[2],
                "avatar_url": webp_url(row[3]),
                "avatar_cache_path": cache_path(row[4]),
                "avatar_cache_url": cache_url(row[4]),
                "default_avatar_url": default_avatar_url(user_id, row[1]),
                "display_avatar_url": display_avatar_url(user_id, row[1], row[3], row[4]),
                "seen_at": row[5],
            }
            for row in history
        ]
    )


@app.route("/users/<int:user_id>/guilds", methods=["GET"])
def get_user_guilds(user_id):
    guilds = db.fetchall(
        """
        SELECT g.id, g.name, g.icon_url, g.icon_cache_path, m.first_seen, m.last_seen
        FROM guild_memberships m
        JOIN guilds g ON g.id = m.guild_id
        WHERE m.user_id = %s
        ORDER BY m.last_seen DESC NULLS LAST
        """,
        (user_id,),
    )

    return jsonify(
        [
            {
                "id": snowflake(g[0]),
                "name": g[1],
                "icon_url": webp_url(g[2]),
                "icon_cache_path": cache_path(g[3]),
                "icon_cache_url": cache_url(g[3]),
                "first_seen": g[4],
                "last_seen": g[5],
            }
            for g in guilds
        ]
    )


@app.route("/users/<int:user_id>/messages", methods=["GET"])
def get_user_messages(user_id):
    limit = message_page_size()
    before = request.args.get("before", type=int)
    before_clause, before_params = message_cursor_clause(before)

    messages = db.fetchall(
        f"""
        SELECT m.id, m.guild_id, g.name, m.channel_id, c.name, m.created_at, m.content
        FROM messages m
        LEFT JOIN guilds g ON g.id = m.guild_id
        LEFT JOIN channels c ON c.id = m.channel_id
        WHERE m.user_id = %s
            {before_clause}
        ORDER BY m.id DESC
        LIMIT %s
        """,
        (user_id, *before_params, limit),
    )
    media_by_message = media_for_messages(messages)

    return jsonify([serialize_message(row, media_by_message) for row in messages])


@app.route("/guilds", methods=["GET"])
def list_guilds():
    query = request.args.get("q", "").strip()
    limit = min(request.args.get("limit", 50, type=int), 200)

    if query.isdigit():
        rows = db.fetchall(
            """
            SELECT id, name, icon_url, icon_cache_path, first_seen, last_scraped
            FROM guilds
            WHERE id = %s OR name ILIKE %s
            ORDER BY last_scraped DESC NULLS LAST
            LIMIT %s
            """,
            (int(query), f"%{query}%", limit),
        )
    else:
        rows = db.fetchall(
            """
            SELECT id, name, icon_url, icon_cache_path, first_seen, last_scraped
            FROM guilds
            WHERE name ILIKE %s
            ORDER BY last_scraped DESC NULLS LAST
            LIMIT %s
            """,
            (f"%{query}%", limit),
        )

    return jsonify([serialize_guild_row(row) for row in rows])


@app.route("/guilds/<int:guild_id>", methods=["GET"])
def get_guild(guild_id):
    guild = db.fetchone(
        """
        SELECT id, name, icon, icon_url, icon_cache_path, first_seen, last_scraped
        FROM guilds
        WHERE id = %s
        """,
        (guild_id,),
    )

    if not guild:
        abort(404, description="Guild not found")

    return jsonify(
        {
            "id": snowflake(guild[0]),
            "name": guild[1],
            "icon": guild[2],
            "icon_url": webp_url(guild[3]),
            "icon_cache_path": cache_path(guild[4]),
            "icon_cache_url": cache_url(guild[4]),
            "first_seen": guild[5],
            "last_scraped": guild[6],
        }
    )


@app.route("/guilds/<int:guild_id>/history", methods=["GET"])
def get_guild_history(guild_id):
    history = db.fetchall(
        """
        SELECT name, icon, icon_url, icon_cache_path, seen_at
        FROM guild_profile_history
        WHERE guild_id = %s
        ORDER BY seen_at DESC
        """,
        (guild_id,),
    )

    return jsonify(
        [
            {
                "name": row[0],
                "icon": row[1],
                "icon_url": webp_url(row[2]),
                "icon_cache_path": cache_path(row[3]),
                "icon_cache_url": cache_url(row[3]),
                "seen_at": row[4],
            }
            for row in history
        ]
    )


@app.route("/guilds/<int:guild_id>/members", methods=["GET"])
def get_guild_members(guild_id):
    members = db.fetchall(
        """
        SELECT u.id, u.username, u.discriminator, u.avatar_url, u.avatar_cache_path, m.first_seen, m.last_seen
        FROM guild_memberships m
        JOIN users u ON u.id = m.user_id
        WHERE m.guild_id = %s
        ORDER BY m.last_seen DESC NULLS LAST
        """,
        (guild_id,),
    )

    return jsonify(
        [
            {
                "id": snowflake(u[0]),
                "username": u[1],
                "discriminator": u[2],
                "avatar_url": webp_url(u[3]),
                "avatar_cache_path": cache_path(u[4]),
                "avatar_cache_url": cache_url(u[4]),
                "default_avatar_url": default_avatar_url(u[0], u[2]),
                "display_avatar_url": display_avatar_url(u[0], u[2], u[3], u[4]),
                "first_seen": u[5],
                "last_seen": u[6],
            }
            for u in members
        ]
    )


@app.route("/guilds/<int:guild_id>/channels", methods=["GET"])
def get_guild_channels(guild_id):
    channels = db.fetchall(
        """
        WITH raw_channel_ids AS (
            SELECT id AS channel_id, name
            FROM channels
            WHERE guild_id = %s
            UNION
            SELECT channel_id, NULL AS name
            FROM messages
            WHERE guild_id = %s
        ),
        channel_ids AS (
            SELECT channel_id, MAX(name) AS name
            FROM raw_channel_ids
            GROUP BY channel_id
        )
        SELECT
            ci.channel_id,
            ci.name,
            COUNT(m.id) AS message_count,
            MAX(m.created_at) AS last_message_at
        FROM channel_ids ci
        LEFT JOIN messages m ON m.guild_id = %s AND m.channel_id = ci.channel_id
        GROUP BY ci.channel_id, ci.name
        ORDER BY last_message_at DESC NULLS LAST, name ASC NULLS LAST
        """,
        (guild_id, guild_id, guild_id),
    )

    return jsonify(
        [
            {
                "id": snowflake(row[0]),
                "name": row[1] or str(row[0]),
                "message_count": row[2],
                "last_message_at": row[3],
            }
            for row in channels
        ]
    )


@app.route("/guilds/<int:guild_id>/messages", methods=["GET"])
def get_guild_messages(guild_id):
    limit = message_page_size()
    before = request.args.get("before", type=int)
    before_clause, before_params = message_cursor_clause(before)

    messages = db.fetchall(
        f"""
        SELECT m.id, m.guild_id, g.name, m.channel_id, c.name, m.created_at, m.content, u.id, u.username
        FROM messages m
        LEFT JOIN guilds g ON g.id = m.guild_id
        LEFT JOIN channels c ON c.id = m.channel_id
        LEFT JOIN users u ON u.id = m.user_id
        WHERE m.guild_id = %s
            {before_clause}
        ORDER BY m.id DESC
        LIMIT %s
        """,
        (guild_id, *before_params, limit),
    )
    media_by_message = media_for_messages(messages)

    return jsonify([serialize_message(row, media_by_message, include_author=True) for row in messages])


@app.route("/guilds/<int:guild_id>/channels/<int:channel_id>/messages", methods=["GET"])
def get_channel_messages(guild_id, channel_id):
    limit = message_page_size()
    before = request.args.get("before", type=int)
    before_clause, before_params = message_cursor_clause(before)

    messages = db.fetchall(
        f"""
        SELECT m.id, m.guild_id, g.name, m.channel_id, c.name, m.created_at, m.content, u.id, u.username
        FROM messages m
        LEFT JOIN guilds g ON g.id = m.guild_id
        LEFT JOIN channels c ON c.id = m.channel_id
        LEFT JOIN users u ON u.id = m.user_id
        WHERE m.guild_id = %s AND m.channel_id = %s
            {before_clause}
        ORDER BY m.id DESC
        LIMIT %s
        """,
        (guild_id, channel_id, *before_params, limit),
    )
    media_by_message = media_for_messages(messages)

    return jsonify([serialize_message(row, media_by_message, include_author=True) for row in messages])


def media_for_messages(messages):
    message_ids = [row[0] for row in messages]
    if not message_ids:
        return {}

    rows = db.fetchall(
        """
        SELECT
            message_id,
            kind,
            url,
            proxy_url,
            filename,
            content_type,
            size_bytes,
            width,
            height,
            metadata
        FROM message_media
        WHERE message_id = ANY(%s)
        ORDER BY message_id, media_index
        """,
        (message_ids,),
    )

    media_by_message = defaultdict(list)
    for row in rows:
        media_by_message[row[0]].append(
            {
                "kind": row[1],
                "url": row[2],
                "proxy_url": row[3],
                "filename": row[4],
                "content_type": row[5],
                "size_bytes": row[6],
                "width": row[7],
                "height": row[8],
                "metadata": row[9],
            }
        )

    return media_by_message


def cache_url(cache_path):
    normalized = normalized_cache_path(cache_path)
    if not normalized:
        return None

    try:
        relative = normalized.relative_to(Path(MEDIA_CACHE_DIR))
    except ValueError:
        parts = normalized.parts
        cache_name = Path(MEDIA_CACHE_DIR).name
        relative = Path(*parts[parts.index(cache_name) + 1 :]) if cache_name in parts else normalized

    return f"/cache/{relative.as_posix()}"


def cache_path(cache_path):
    normalized = normalized_cache_path(cache_path)
    return str(normalized) if normalized else None


def normalized_cache_path(cache_path):
    if not cache_path:
        return None

    normalized = Path(cache_path)
    if normalized.suffix.lower() == ".webp":
        return normalized

    webp_path = normalized.with_suffix(".webp")
    return webp_path if webp_path.exists() else None


def webp_url(url):
    if not url:
        return None

    parsed = urlsplit(url)
    path = str(Path(parsed.path).with_suffix(".webp")).replace("\\", "/")
    return urlunsplit((parsed.scheme, parsed.netloc, path, parsed.query, parsed.fragment))


def default_avatar_url(user_id, discriminator):
    if discriminator and discriminator != "0":
        index = int(discriminator) % 5
    else:
        index = (int(user_id) >> 22) % 6

    return f"https://cdn.discordapp.com/embed/avatars/{index}.png"


def display_avatar_url(user_id, discriminator, avatar_url, avatar_cache_path):
    return cache_url(avatar_cache_path) or webp_url(avatar_url) or default_avatar_url(
        user_id, discriminator
    )


def message_page_size():
    return min(request.args.get("limit", 100, type=int), 150)


def message_cursor_clause(before):
    if before is None:
        return "", ()

    return "AND m.id < %s", (before,)


def serialize_user_row(row):
    return {
        "id": snowflake(row[0]),
        "username": row[1],
        "discriminator": row[2],
        "avatar_url": webp_url(row[3]),
        "avatar_cache_path": cache_path(row[4]),
        "avatar_cache_url": cache_url(row[4]),
        "default_avatar_url": default_avatar_url(row[0], row[2]),
        "display_avatar_url": display_avatar_url(row[0], row[2], row[3], row[4]),
        "first_seen": row[5],
        "last_seen": row[6],
    }


def serialize_guild_row(row):
    return {
        "id": snowflake(row[0]),
        "name": row[1],
        "icon_url": webp_url(row[2]),
        "icon_cache_path": cache_path(row[3]),
        "icon_cache_url": cache_url(row[3]),
        "first_seen": row[4],
        "last_scraped": row[5],
    }


def serialize_message(row, media_by_message, include_author=False):
    data = {
        "id": snowflake(row[0]),
        "guild_id": snowflake(row[1]),
        "guild_name": row[2],
        "channel_id": snowflake(row[3]),
        "channel_name": row[4],
        "created_at": row[5],
        "content": row[6],
        "media": media_by_message.get(row[0], []),
    }

    if include_author:
        data["user_id"] = snowflake(row[7])
        data["username"] = row[8]

    return data


def snowflake(value):
    return str(value) if value is not None else None


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
