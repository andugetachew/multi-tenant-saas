# organizations/utils.py
from django.http import JsonResponse


def check_plan_limit_middleware(get_response):
    """Middleware to check plan limits"""

    def middleware(request):
        if request.user.is_authenticated:
            org = request.user.organization
            if org and org.plan == "free":
                # Add free plan restrictions here
                pass
        return get_response(request)

    return middleware
