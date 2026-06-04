from django.http import JsonResponse
from .models import Organization


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        org_id = request.headers.get("X-Organization-ID")

        if org_id and request.user.is_authenticated:
            try:
                organization = Organization.objects.get(id=org_id)

                if (
                    request.user.organization
                    and request.user.organization.id != organization.id
                ):
                    return JsonResponse(
                        {"error": "Access denied to this organization"}, status=403
                    )

                request.organization = organization
            except Organization.DoesNotExist:
                return JsonResponse({"error": "Invalid organization"}, status=400)

        elif request.user.is_authenticated and request.user.organization:
            request.organization = request.user.organization
        else:
            request.organization = None

        return self.get_response(request)
