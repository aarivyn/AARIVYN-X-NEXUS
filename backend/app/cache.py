import json
from typing import Optional, Any
from config import settings

_memory_cache = {}

try:
    import redis
    redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=2)
    redis_client.ping()
    print(f"[+] Connected to Redis Cache: {settings.REDIS_URL}")
    USE_REDIS = True
except Exception:
    print("[!] Redis Cache unreachable. Using in-memory fallback cache.")
    USE_REDIS = False
    redis_client = None

def get_cache(key: str) -> Optional[Any]:
    if USE_REDIS and redis_client:
        try:
            val = redis_client.get(key)
            return json.loads(val) if val else None
        except Exception:
            pass
    return _memory_cache.get(key)

def set_cache(key: str, value: Any, ttl_seconds: int = 3600):
    if USE_REDIS and redis_client:
        try:
            redis_client.setex(key, ttl_seconds, json.dumps(value))
            return
        except Exception:
            pass
    _memory_cache[key] = value

def delete_cache(key: str):
    if USE_REDIS and redis_client:
        try:
            redis_client.delete(key)
            return
        except Exception:
            pass
    _memory_cache.pop(key, None)
