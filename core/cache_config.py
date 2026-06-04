# core/cache_config.py
from django.core.cache import cache
from django.conf import settings
import redis
import json
import hashlib


class CacheService:
    """Enterprise-grade caching with automatic invalidation"""

    CACHE_TTL = {
        "dashboard_stats": 300,  # 5 minutes
        "realtime_dashboard": 180,  # 3 minutes
        "project_list": 120,  # 2 minutes
        "search_results": 60,  # 1 minute
        "organization_details": 600,  # 10 minutes
    }

    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )

    def get_or_set(self, key, callback, ttl=None):
        """Get from cache or execute callback and cache result"""
        cached = self.redis_client.get(key)
        if cached:
            return json.loads(cached)

        result = callback()
        self.redis_client.setex(key, ttl or 300, json.dumps(result))
        return result

    def invalidate_pattern(self, pattern):
        """Invalidate all keys matching pattern"""
        keys = self.redis_client.keys(pattern)
        if keys:
            self.redis_client.delete(*keys)

    def generate_key(self, prefix, *args, **kwargs):
        """Generate deterministic cache key"""
        key_string = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_string.encode()).hexdigest()


cache_service = CacheService()
