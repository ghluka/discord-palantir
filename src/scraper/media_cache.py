import os
import sys
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MEDIA_CACHE_DIR, MEDIA_CACHE_IMAGE_SIZE, MEDIA_CACHE_WEBP_QUALITY


CDN_BASE_URL = "https://cdn.discordapp.com"
CACHE_EXTENSION = "webp"


def user_avatar_url(user):
    avatar_hash = user.get("avatar")
    if not avatar_hash:
        return None

    return f"{CDN_BASE_URL}/avatars/{user['id']}/{avatar_hash}.webp?size={MEDIA_CACHE_IMAGE_SIZE}"


def guild_icon_url(guild):
    icon_hash = guild.get("icon")
    if not icon_hash:
        return None

    return f"{CDN_BASE_URL}/icons/{guild['id']}/{icon_hash}.webp?size={MEDIA_CACHE_IMAGE_SIZE}"


def cache_remote_asset(kind, entity_id, asset_hash, url):
    if not asset_hash or not url:
        return None

    target = Path(MEDIA_CACHE_DIR) / kind / str(entity_id) / f"{asset_hash}.{CACHE_EXTENSION}"
    if target.exists():
        return str(target)

    target.parent.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        image.seek(0)
        image.thumbnail(
            (MEDIA_CACHE_IMAGE_SIZE, MEDIA_CACHE_IMAGE_SIZE), Image.Resampling.LANCZOS
        )
        image.save(
            target,
            format="WEBP",
            quality=MEDIA_CACHE_WEBP_QUALITY,
            method=6,
        )
    except (OSError, requests.RequestException):
        return None

    return str(target)
