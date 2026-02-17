from flask import Flask, abort, jsonify, request

from db import Database

app = Flask(__name__)
db = Database()


@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = db.fetchone(
        "SELECT id, username, discriminator, first_seen, last_seen FROM users WHERE id = %s",
        (user_id,),
    )

    if not user:
        abort(404, description="User not found")

    return jsonify(
        {
            "id": user[0],
            "username": user[1],
            "discriminator": user[2],
            "first_seen": user[3],
            "last_seen": user[4],
        }
    )


@app.route("/users/<int:user_id>/guilds", methods=["GET"])
def get_user_guilds(user_id):
    guilds = db.fetchall(
        """
        SELECT g.id, g.name, m.first_seen, m.last_seen
        FROM guild_memberships m
        JOIN guilds g ON g.id = m.guild_id
        WHERE m.user_id = %s
        """,
        (user_id,),
    )

    return jsonify(
        [
            {"id": g[0], "name": g[1], "first_seen": g[2], "last_seen": g[3]}
            for g in guilds
        ]
    )


@app.route("/users/<int:user_id>/messages", methods=["GET"])
def get_user_messages(user_id):
    limit = request.args.get("limit", 50, type=int)

    messages = db.fetchall(
        """
        SELECT id, guild_id, channel_id, created_at, content
        FROM messages
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (user_id, limit),
    )

    return jsonify(
        [
            {
                "id": m[0],
                "guild_id": m[1],
                "channel_id": m[2],
                "created_at": m[3],
                "content": m[4],
            }
            for m in messages
        ]
    )


@app.route("/guilds/<int:guild_id>", methods=["GET"])
def get_guild(guild_id):
    guild = db.fetchone(
        "SELECT id, name, first_seen, last_scraped FROM guilds WHERE id = %s",
        (guild_id,),
    )

    if not guild:
        abort(404, description="Guild not found")

    return jsonify(
        {
            "id": guild[0],
            "name": guild[1],
            "first_seen": guild[2],
            "last_scraped": guild[3],
        }
    )


@app.route("/guilds/<int:guild_id>/members", methods=["GET"])
def get_guild_members(guild_id):
    members = db.fetchall(
        """
        SELECT u.id, u.username, u.discriminator, m.first_seen, m.last_seen
        FROM guild_memberships m
        JOIN users u ON u.id = m.user_id
        WHERE m.guild_id = %s
        """,
        (guild_id,),
    )

    return jsonify(
        [
            {
                "id": u[0],
                "username": u[1],
                "discriminator": u[2],
                "first_seen": u[3],
                "last_seen": u[4],
            }
            for u in members
        ]
    )


@app.route("/guilds/<int:guild_id>/messages", methods=["GET"])
def get_guild_messages(guild_id):
    limit = request.args.get("limit", 50, type=int)

    messages = db.fetchall(
        """
        SELECT id, channel_id, user_id, created_at, content
        FROM messages
        WHERE guild_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (guild_id, limit),
    )

    return jsonify(
        [
            {
                "id": m[0],
                "channel_id": m[1],
                "user_id": m[2],
                "created_at": m[3],
                "content": m[4],
            }
            for m in messages
        ]
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
