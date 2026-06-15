import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

BASE_URL = "https://discord.com/api/v10"
DISCORD_RETRY_ATTEMPTS = int(os.getenv("DISCORD_RETRY_ATTEMPTS", "8"))
DISCORD_RETRY_BASE_DELAY = float(os.getenv("DISCORD_RETRY_BASE_DELAY", "2"))
DISCORD_RETRY_MAX_DELAY = float(os.getenv("DISCORD_RETRY_MAX_DELAY", "60"))
MEDIA_CACHE_DIR = Path(os.getenv("MEDIA_CACHE_DIR", "media_cache"))
MEDIA_CACHE_IMAGE_SIZE = int(os.getenv("MEDIA_CACHE_IMAGE_SIZE", "256"))
MEDIA_CACHE_WEBP_QUALITY = int(os.getenv("MEDIA_CACHE_WEBP_QUALITY", "70"))
