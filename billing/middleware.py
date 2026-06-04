from django.http import JsonResponse
from .utils import check_org_limit, check_feature_access


class PlanLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            org = request.user.organization

            # Check project creation limits
            if request.path.startswith("/api/projects/") and request.method == "POST":
                if not check_org_limit(org, "projects"):
                    return JsonResponse(
                        {"error": "Project limit reached. Please upgrade your plan."},
                        status=403,
                    )

            # Check user invitation limits
            if (
                request.path.startswith("/api/organizations/invite/")
                and request.method == "POST"
            ):
                if not check_org_limit(org, "users"):
                    return JsonResponse(
                        {"error": "User limit reached. Please upgrade your plan."},
                        status=403,
                    )

            # Check feature access
            if "/api/dashboard/realtime/" in request.path and request.method == "GET":
                if not check_feature_access(org, "realtime_analytics"):
                    return JsonResponse(
                        {
                            "error": "Real-time analytics is not available on your plan. Upgrade to Pro or Enterprise."
                        },
                        status=403,
                    )

            if "/api/reports/advanced/" in request.path and request.method == "GET":
                if not check_feature_access(org, "advanced_exports"):
                    return JsonResponse(
                        {"error": "Advanced exports require Pro or Enterprise plan."},
                        status=403,
                    )

        return self.get_response(request)
