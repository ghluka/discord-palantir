import os
import sys
import time
from random import uniform
from json import dumps, loads
from threading import Thread
from time import sleep

import requests
from websocket import WebSocketApp

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    BASE_URL,
    DISCORD_RETRY_ATTEMPTS,
    DISCORD_RETRY_BASE_DELAY,
    DISCORD_RETRY_MAX_DELAY,
)


class DiscordClient:

    def __init__(self, token: str):
        self.headers = {"Authorization": token}

    def _get(self, endpoint, params=None):
        attempts = 0

        while True:
            try:
                r = requests.get(
                    BASE_URL + endpoint,
                    headers=self.headers,
                    params=params,
                    timeout=30,
                )
            except requests.exceptions.RequestException as ex:
                attempts += 1
                if attempts >= DISCORD_RETRY_ATTEMPTS:
                    raise

                retry = self._retry_delay(attempts)
                print(
                    f"Network error for {endpoint}; retrying in {retry:.1f}s "
                    f"({attempts}/{DISCORD_RETRY_ATTEMPTS}): {ex}"
                )
                time.sleep(retry)
                continue

            # print(BASE_URL + endpoint, params)
            if r.status_code == 429:
                retry = r.json().get("retry_after", 5)
                time.sleep(retry)
                continue

            if r.status_code >= 500:
                attempts += 1
                if attempts >= DISCORD_RETRY_ATTEMPTS:
                    r.raise_for_status()

                retry = self._retry_delay(attempts)
                print(
                    f"Discord returned {r.status_code} for {endpoint}; "
                    f"retrying in {retry:.1f}s ({attempts}/{DISCORD_RETRY_ATTEMPTS})"
                )
                time.sleep(retry)
                continue

            try:
                # print(r.status_code)
                r.raise_for_status()
                # print(r.json())
                return r.json()
            except requests.exceptions.HTTPError as ex:
                # print(endpoint, ex)
                return {}

    def _retry_delay(self, attempts):
        delay = DISCORD_RETRY_BASE_DELAY * (2 ** (attempts - 1))
        return min(delay + uniform(0, 1), DISCORD_RETRY_MAX_DELAY)

    def get_guilds(self):
        return self._get("/users/@me/guilds")

    def get_channels(self, guild_id):
        return self._get(f"/guilds/{guild_id}/channels")

    def get_messages(self, channel_id, after=None, before=None):
        params = {"limit": 100}
        if after:
            params["after"] = after
        if before:
            params["before"] = before

        return self._get(f"/channels/{channel_id}/messages", params=params)
