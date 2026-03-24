import json
import redis
from typing import Optional, Any
from app.core.config import settings

_redis_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


class Cache:
    """Simple Redis cache wrapper."""

    def __init__(self):
        self.redis = get_redis()

    def get(self, key: str) -> Optional[Any]:
        try:
            value = self.redis.get(key)
            return json.loads(value) if value else None
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        try:
            self.redis.setex(key, ttl, json.dumps(value, default=str))
            return True
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        try:
            self.redis.delete(key)
            return True
        except Exception:
            return False

    def delete_pattern(self, pattern: str) -> int:
        try:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
        except Exception:
            return 0


# Cache key helpers
def restaurant_cache_key(restaurant_id: str) -> str:
    return f"restaurant:{restaurant_id}"


def menu_cache_key(restaurant_id: str) -> str:
    return f"menu:{restaurant_id}"


def restaurants_list_key(city: str = "all", cuisine: str = "all") -> str:
    return f"restaurants:list:{city}:{cuisine}"
