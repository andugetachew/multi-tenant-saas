from .models import AuditLog

METHOD_TO_ACTION = {
    "POST": "CREATE",
    "PUT": "UPDATE",
    "PATCH": "UPDATE",
    "DELETE": "DELETE",
}


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if (
            request.user.is_authenticated
            and request.user.organization
            and request.method in METHOD_TO_ACTION
        ):
            AuditLog.objects.create(
                organization=request.user.organization,
                user=request.user,
                action=METHOD_TO_ACTION[request.method],
                model_name="API Request",
                object_id=0,
                object_name=request.path,
                ip_address=request.META.get("REMOTE_ADDR", ""),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                old_values={},
                new_values={"method": request.method, "path": request.path},
            )

        return response