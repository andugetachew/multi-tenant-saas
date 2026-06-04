# core/middleware_headers.py
from django.core.cache import cache


class RateLimitHeadersMiddleware:
    """Add rate limit headers to all responses"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Add rate limit headers
        if hasattr(request, "rate_limit_info"):
            response["X-RateLimit-Limit"] = str(
                request.rate_limit_info.get("limit", "")
            )
            response["X-RateLimit-Remaining"] = str(
                request.rate_limit_info.get("remaining", "")
            )
            response["X-RateLimit-Reset"] = str(
                request.rate_limit_info.get("reset", "")
            )
            response["Retry-After"] = str(
                request.rate_limit_info.get("retry_after", "")
            )

        return response
