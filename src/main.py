import argparse
import os

from dotenv import load_dotenv

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--token")
    args = parser.parse_args()

    if args.token:
        os.environ["DISCORD_TOKEN"] = args.token
        load_dotenv(override=False)

    from sync import run_sync

    run_sync()
