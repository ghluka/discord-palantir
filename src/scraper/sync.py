import argparse

from db import Database
from discord_client import DiscordClient
from ingestor import Ingestor


def run_sync(token: str):
    db = Database()
    client = DiscordClient(token)
    ingestor = Ingestor(db, client)

    guilds = client.get_guilds()

    for guild in guilds:
        ingestor.sync_guild(guild)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--token")
    args = parser.parse_args()

    if args.token:
        run_sync(args.token)
