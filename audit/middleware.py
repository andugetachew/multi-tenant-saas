from .models import AuditLog


class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Log user actions
        if request.user.is_authenticated and request.method in [
            "POST",
            "PUT",
            "DELETE",
        ]:
            AuditLog.objects.create(
                organization=request.user.organization,
                user=request.user,
                action=request.method,
                model_name="API Request",
                object_id=0,
                object_name=request.path,
                ip_address=request.META.get("REMOTE_ADDR", ""),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                old_values={},
                new_values={"method": request.method, "path": request.path},
            )

        return response
