import json
import pytest
from unittest.mock import MagicMock, patch

from core.cache_config import CacheService, cache_service


class TestGetOrSet:
    def test_returns_cached_value_when_present(self):
        service = CacheService.__new__(CacheService)
        service.redis_client = MagicMock()
        service.redis_client.get.return_value = json.dumps({"cached": True})

        callback = MagicMock()
        result = service.get_or_set("key", callback)

        assert result == {"cached": True}
        callback.assert_not_called()

    def test_computes_and_caches_when_missing(self):
        service = CacheService.__new__(CacheService)
        service.redis_client = MagicMock()
        service.redis_client.get.return_value = None

        callback = MagicMock(return_value={"fresh": True})
        result = service.get_or_set("key", callback, ttl=60)

        assert result == {"fresh": True}
        service.redis_client.setex.assert_called_once_with("key", 60, json.dumps({"fresh": True}))

    def test_uses_default_ttl_when_none_provided(self):
        service = CacheService.__new__(CacheService)
        service.redis_client = MagicMock()
        service.redis_client.get.return_value = None

        service.get_or_set("key", lambda: {"a": 1})

        args = service.redis_client.setex.call_args[0]
        assert args[1] == 300


class TestInvalidatePattern:
    def test_deletes_matching_keys(self):
        service = CacheService.__new__(CacheService)
        service.redis_client = MagicMock()
        service.redis_client.keys.return_value = ["key1", "key2"]

        service.invalidate_pattern("prefix:*")

        service.redis_client.delete.assert_called_once_with("key1", "key2")

    def test_no_delete_call_when_no_matching_keys(self):
        service = CacheService.__new__(CacheService)
        service.redis_client = MagicMock()
        service.redis_client.keys.return_value = []

        service.invalidate_pattern("prefix:*")

        service.redis_client.delete.assert_not_called()


class TestGenerateKey:
    def test_deterministic_for_same_inputs(self):
        service = CacheService.__new__(CacheService)
        key1 = service.generate_key("prefix", 1, 2, a=3)
        key2 = service.generate_key("prefix", 1, 2, a=3)
        assert key1 == key2

    def test_different_for_different_inputs(self):
        service = CacheService.__new__(CacheService)
        key1 = service.generate_key("prefix", 1)
        key2 = service.generate_key("prefix", 2)
        assert key1 != key2


class TestCacheServiceSingleton:
    def test_cache_service_has_ttl_config(self):
        assert cache_service.CACHE_TTL["dashboard_stats"] == 300