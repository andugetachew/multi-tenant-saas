# core/redis_config.py
import redis
from redis.connection import ConnectionPool
from django.conf import settings
import time
import logging

logger = logging.getLogger(__name__)


class ResilientRedisClient:
    """FAANG-level: Circuit breaker + connection pooling for Redis"""

    def __init__(self):
        self.pool = ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            max_connections=50,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        self.client = redis.Redis(connection_pool=self.pool)
        self.failure_count = 0
        self.last_failure_time = None
        self.circuit_open = False

    def get(self, key, fallback=None):
        """Get with circuit breaker"""
        if self.circuit_open:
            if time.time() - self.last_failure_time > 30:
                self.circuit_open = False
                self.failure_count = 0
            else:
                logger.warning(f"Redis circuit open, using fallback for key {key}")
                return fallback

        try:
            result = self.client.get(key)
            self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= 5:
                self.circuit_open = True
                logger.error(
                    f"Redis circuit opened after {self.failure_count} failures"
                )
            return fallback

    def setex(self, key, ttl, value):
        """Set with retry"""
        for attempt in range(3):
            try:
                return self.client.setex(key, ttl, value)
            except Exception as e:
                if attempt == 2:
                    logger.error(f"Failed to set Redis key after 3 attempts: {key}")
                    return None
                time.sleep(0.1 * (2**attempt))


redis_client = ResilientRedisClient()
