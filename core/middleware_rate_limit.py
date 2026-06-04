from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings


class GlobalRateLimitMiddleware:
    """Defense in depth - global rate limiting before reaching views"""

    GLOBAL_LIMITS = {
        "DEFAULT": {"limit": 100, "window": 60},
        "/api/auth/": {"limit": 30, "window": 60},
        "/api/search/": {"limit": 20, "window": 60},
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
    
        if getattr(settings, "TESTING", False):
            return self.get_response(request)


        if request.path.startswith("/admin/") or request.path.startswith("/static/"):
            return self.get_response(request)

     
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")

    
        limit = self.GLOBAL_LIMITS["DEFAULT"]["limit"]
        window = self.GLOBAL_LIMITS["DEFAULT"]["window"]
        for path_pattern, limits in self.GLOBAL_LIMITS.items():
            if request.path.startswith(path_pattern):
                limit = limits["limit"]
                window = limits["window"]
                break

       
        cache_key = f"global_ratelimit:{ip}:{request.path}"
        current = cache.get(cache_key, 0)
        if current >= limit:
            return JsonResponse(
                {
                    "error": "Too many requests",
                    "retry_after": window,
                    "limit": limit,
                    "window": window,
                },
                status=429,
            )
        cache.set(cache_key, current + 1, window)
        return self.get_response(request)