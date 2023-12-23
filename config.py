# config.py
from datetime import timedelta

STORE_CACHE_IN_MEMORY = False  # False - if change you want to store files in a cache folder
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
CACHE_DIR = 'cache_data'
FILES_DIR = 'cache_data/uploads'
IMAGE_SIZES = {
    "small": 320,
    "medium": 640,
    "large": 1280
}
EXPIRATION_SECONDS = 3600 * 24 * 365
REDIS_KEY_PREFIX = "cached_cdn_server:"
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
