from functools import wraps
from .models import ActivityLog


def log_activity(action):
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            response = func(self, request, *args, **kwargs)

            # Log activity if request successful
            if response.status_code in [200, 201, 204]:
                # Get object name from response
                object_name = ""
                if hasattr(response, "data") and response.data:
                    if isinstance(response.data, dict):
                        object_name = response.data.get(
                            "name", str(response.data.get("id", ""))
                        )

                ActivityLog.objects.create(
                    organization=request.user.organization,
                    user=request.user,
                    action=action,
                    model_name=self.__class__.__name__.replace("View", ""),
                    object_id=kwargs.get("pk", 0),
                    object_name=object_name,
                    ip_address=getattr(request, "client_ip", ""),
                    changes={},
                )
            return response

        return wrapper

    return decorator
