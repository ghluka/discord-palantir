import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from db import Database
from discord_client import DiscordClient
from ingestor import Ingestor


def sync_one_guild(token, guild):
    db = Database(ensure_schema=False)
    client = DiscordClient(token)
    ingestor = Ingestor(db, client)

    try:
        ingestor.sync_guild(guild)
    finally:
        db.close()


def run_sync(token: str, workers: int = 4):
    db = Database()
    client = DiscordClient(token)

    try:
        guilds = client.get_guilds()
    finally:
        db.close()

    if not guilds:
        print("No guilds found.")
        return

    if workers <= 1:
        for guild in guilds:
            sync_one_guild(token, guild)
        return

    max_workers = min(workers, len(guilds))
    print(f"Syncing {len(guilds)} guilds with {max_workers} workers")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(sync_one_guild, token, guild): guild for guild in guilds
        }
        failures = 0

        for future in as_completed(futures):
            guild = futures[future]
            try:
                future.result()
            except Exception as ex:
                failures += 1
                print(f"Failed syncing {guild.get('name', guild.get('id'))}: {ex}")

    if failures:
        raise SystemExit(f"{failures} guild sync(s) failed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--token")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    if args.token:
        run_sync(args.token, args.workers)
