from django.core.cache import cache
from django.utils import timezone
import hashlib


class RateLimiter:
    """
    Simple but production-safe rate limiter for SaaS APIs
    """

    def __init__(self, limit=10, window=60):
        self.limit = limit        # max requests
        self.window = window      # time window in seconds

    def get_key(self, request, scope="default"):
        """
        Generate unique rate limit key per user/IP + scope
        Works well for multi-tenant SaaS
        """

        user_id = getattr(request.user, "id", None)
        ip = self.get_ip(request)

        raw_key = f"{scope}:{user_id}:{ip}"
        return hashlib.sha256(raw_key.encode()).hexdigest()

    def get_ip(self, request):
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded:
            return x_forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

    def is_allowed(self, request, scope="default"):
        key = self.get_key(request, scope)
        now = timezone.now().timestamp()

        data = cache.get(key)

        if not data:
            cache.set(key, {"count": 1, "start": now}, self.window)
            return True

        elapsed = now - data["start"]

        if elapsed > self.window:
            cache.set(key, {"count": 1, "start": now}, self.window)
            return True

        if data["count"] >= self.limit:
            return False

        data["count"] += 1
        cache.set(key, data, self.window)
        return True


rate_limiter = RateLimiter(limit=5, window=60)