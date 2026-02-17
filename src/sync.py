from db import Database
from discord_client import DiscordClient
from ingestor import Ingestor


def run_sync():
    db = Database()
    client = DiscordClient()
    ingestor = Ingestor(db, client)

    guilds = client.get_guilds()

    for guild in guilds:
        ingestor.sync_guild(guild)
