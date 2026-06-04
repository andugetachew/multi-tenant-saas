# core/rate_limits.py
from django.core.cache import cache
from rest_framework.throttling import BaseThrottle
from rest_framework.exceptions import Throttled
import time
import hashlib


class TieredRateLimiter:
    """FAANG-level: Multi-tier rate limiting with different strategies per endpoint"""

    # Rate limits (requests per time window)
    RATE_LIMITS = {
        # 🔥 AUTHENTICATION ENDPOINTS (Highest Priority)
        "auth_login": {
            "limit": 5,  # 5 attempts
            "window": 60,  # per minute
            "block_duration": 900,  # Block for 15 minutes after exceeded
            "strategy": "ip_user",  # IP + User (if exists)
        },
        "auth_register": {
            "limit": 3,  # 3 registrations
            "window": 60,  # per minute
            "block_duration": 3600,  # Block IP for 1 hour
            "strategy": "ip",
        },
        "auth_password_reset": {
            "limit": 3,  # 3 reset requests
            "window": 3600,  # per hour
            "strategy": "ip_user",
        },
        "auth_verify_email": {
            "limit": 5,  # 5 verification attempts
            "window": 300,  # per 5 minutes
            "strategy": "ip",
        },
        # 🔍 SEARCH ENDPOINTS (Very Important)
        "search_global": {
            "limit": 30,  # 30 searches
            "window": 60,  # per minute
            "strategy": "user_org",
        },
        # 📊 DASHBOARD ENDPOINTS (Important)
        "dashboard_realtime": {
            "limit": 60,  # 60 requests
            "window": 60,  # per minute
            "strategy": "user",
        },
        "dashboard_stats": {
            "limit": 120,  # 120 requests
            "window": 60,  # per minute
            "strategy": "user",
        },
        # 🏢 ORGANIZATION ACTIONS (SaaS Critical)
        "org_invite": {
            "limit": 10,  # 10 invites
            "window": 3600,  # per hour
            "strategy": "org",
        },
        "org_create": {
            "limit": 1,  # 1 org creation
            "window": 86400,  # per day
            "strategy": "ip",
        },
        "org_update": {
            "limit": 30,  # 30 updates
            "window": 3600,  # per hour
            "strategy": "user_org",
        },
        # 📁 PROJECT & TASK CREATION (Moderate)
        "project_create": {
            "limit": 50,  # 50 projects
            "window": 3600,  # per hour
            "strategy": "user_org",
        },
        "task_create": {
            "limit": 200,  # 200 tasks
            "window": 3600,  # per hour
            "strategy": "user_org",
        },
    }

    def __init__(self):
        self.rate_limits = self.RATE_LIMITS

    def get_key(self, request, endpoint_key, strategy):
        """Generate cache key based on strategy"""
        if strategy == "ip":
            return f"ratelimit:{endpoint_key}:ip:{self.get_client_ip(request)}"

        elif strategy == "user":
            if not request.user.is_authenticated:
                return f"ratelimit:{endpoint_key}:anon:{self.get_client_ip(request)}"
            return f"ratelimit:{endpoint_key}:user:{request.user.id}"

        elif strategy == "ip_user":
            key = f"ratelimit:{endpoint_key}:{self.get_client_ip(request)}"
            if request.user.is_authenticated:
                key += f":user:{request.user.id}"
            return key

        elif strategy == "user_org":
            if not request.user.is_authenticated:
                return f"ratelimit:{endpoint_key}:anon:{self.get_client_ip(request)}"
            org_id = getattr(request.user, "organization_id", 0)
            return f"ratelimit:{endpoint_key}:org:{org_id}:user:{request.user.id}"

        elif strategy == "org":
            if not request.user.is_authenticated or not request.user.organization_id:
                return f"ratelimit:{endpoint_key}:anon:{self.get_client_ip(request)}"
            return f"ratelimit:{endpoint_key}:org:{request.user.organization_id}"

        return f"ratelimit:{endpoint_key}:{self.get_client_ip(request)}"

    def get_client_ip(self, request):
        """Get real client IP (handles proxies)"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip

    def check_rate_limit(self, request, endpoint_key):
        """Check if request is within rate limit"""
        if endpoint_key not in self.rate_limits:
            return True, None

        limits = self.rate_limits[endpoint_key]
        cache_key = self.get_key(request, endpoint_key, limits["strategy"])

        # Check if blocked
        block_key = f"{cache_key}:blocked"
        if cache.get(block_key):
            return False, limits.get("block_duration", 900)

        # Get current count
        current = cache.get(cache_key, 0)

        if current >= limits["limit"]:
            # Block further requests
            block_duration = limits.get("block_duration", 900)
            cache.set(block_key, True, block_duration)
            return False, block_duration

        # Increment counter
        cache.set(cache_key, current + 1, limits["window"])

        return True, None


rate_limiter = TieredRateLimiter()


class RateLimitThrottle(BaseThrottle):
    """DRF throttle class for rate limiting"""

    def __init__(self):
        self.endpoint_key = None

    def set_endpoint_key(self, endpoint_key):
        self.endpoint_key = endpoint_key

    def allow_request(self, request, view):
        if not self.endpoint_key:
            return True

        allowed, block_duration = rate_limiter.check_rate_limit(
            request, self.endpoint_key
        )

        if not allowed:
            raise Throttled(
                detail=f"Rate limit exceeded. Try again in {block_duration} seconds."
            )

        return True


# Individual throttle classes for each endpoint
class AuthLoginThrottle(RateLimitThrottle):
    def __init__(self):
        super().__init__()
        self.set_endpoint_key("auth_login")


class AuthRegisterThrottle(RateLimitThrottle):
    def __init__(self):
        super().__init__()
        self.set_endpoint_key("auth_register")


class AuthPasswordResetThrottle(RateLimitThrottle):
    def __init__(self):
        super().__init__()
        self.set_endpoint_key("auth_password_reset")


class AuthVerifyEmailThrottle(RateLimitThrottle):
    def __init__(self):
        super().__init__()
        self.set_endpoint_key("auth_verify_email")


class SearchGlobalThrottle(RateLimitThrottle):
    def __init__(self):
        super().__init__()
        self.set_endpoint_key("search_global")


class DashboardRealtimeThrottle(RateLimitThrottle):
    def __init__(self):
        super().__init__()
        self.set_endpoint_key("dashboard_realtime")


class DashboardStatsThrottle(RateLimitThrottle):
    def __init__(self):
        super().__init__()
        self.set_endpoint_key("dashboard_stats")


class OrgInviteThrottle(RateLimitThrottle):
    def __init__(self):
        super().__init__()
        self.set_endpoint_key("org_invite")


class OrgCreateThrottle(RateLimitThrottle):
    def __init__(self):
        super().__init__()
        self.set_endpoint_key("org_create")


class OrgUpdateThrottle(RateLimitThrottle):
    def __init__(self):
        super().__init__()
        self.set_endpoint_key("org_update")


class ProjectCreateThrottle(RateLimitThrottle):
    def __init__(self):
        super().__init__()
        self.set_endpoint_key("project_create")


class TaskCreateThrottle(RateLimitThrottle):
    def __init__(self):
        super().__init__()
        self.set_endpoint_key("task_create")
