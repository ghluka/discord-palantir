class Ingestor:

    def __init__(self, db, client):
        self.db = db
        self.client = client

    def sync_guild(self, guild):
        guild_id = int(guild["id"])
        print(f"Syncing guild: {guild['name']}")

        from models import Models

        Models.upsert_guild(self.db, guild)

        channels = self.client.get_channels(guild_id)

        for channel in channels:
            Models.upsert_channel(self.db, guild_id, channel)

            if channel["type"] != 0:
                continue

            self.sync_channel(guild_id, int(channel["id"]))

        print(f"Done syncing {guild['name']}")

    def sync_channel(self, guild_id, channel_id):
        from models import Models

        state = self.db.fetchone(
            "SELECT last_message_id FROM channel_state WHERE channel_id=%s",
            (channel_id,),
        )

        after = None
        start = state[0] if state else None
        before = None

        while True:
            messages = self.client.get_messages(channel_id, before=before)

            if not messages:
                # print(f"{channel_id} is empty before {before}!")
                break

            for msg in messages:
                if str(start) == msg["id"]:
                    # print(f"We've already logged up to {start}, cancelling.")
                    return
                Models.upsert_user(self.db, msg["author"])
                if msg["author"].get("id"):
                    Models.upsert_membership(self.db, msg["author"]["id"], guild_id)
                Models.insert_message(self.db, guild_id, channel_id, msg)

            after = start or messages[0]["id"]
            before = messages[-1]["id"]

        if after:
            Models.update_channel_state(self.db, channel_id, after)
        # else:
        # print(f"No more after in {channel_id}?")
