import time
from json import dumps, loads
from threading import Thread
from time import sleep

import requests
from websocket import WebSocketApp

from config import BASE_URL, DISCORD_TOKEN


class DiscordClient:

    def __init__(self):
        self.headers = {"Authorization": DISCORD_TOKEN}

    def _get(self, endpoint, params=None):
        while True:
            r = requests.get(BASE_URL + endpoint, headers=self.headers, params=params)
            # print(BASE_URL + endpoint, params)
            if r.status_code == 429:
                retry = r.json().get("retry_after", 5)
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
