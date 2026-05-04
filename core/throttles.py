from rest_framework.throttling import UserRateThrottle


class BurstRateThrottle(UserRateThrottle):
    rate = "60/min"


class SustainedRateThrottle(UserRateThrottle):
    rate = "1000/hour"


class OrganizationRateThrottle(UserRateThrottle):
    """Rate limit based on organization"""

    def get_cache_key(self, request, view):
        if request.user.is_authenticated and request.user.organization:
            return f"org_{request.user.organization.id}"
        return super().get_cache_key(request, view)
