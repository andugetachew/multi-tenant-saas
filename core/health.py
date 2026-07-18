# core/health.py
from datetime import datetime  # Add this import
from django.http import JsonResponse
from django.db import connections
from django.db.utils import OperationalError
from django.core.cache import cache


def health_check(request):
    health_status = {
        "status": "healthy",
        "timestamp": str(datetime.now()),  # Now datetime is imported
        "checks": {},
    }

    # Database check
    try:
        connections["default"].cursor()
        health_status["checks"]["database"] = "up"
    except OperationalError:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = "down"

    # Cache check
    
    try:
        cache.set("health_check", "ok", 10)
        if cache.get("health_check") == "ok":
            health_status["checks"]["cache"] = "up"
        else:
            health_status["status"] = "unhealthy"
            health_status["checks"]["cache"] = "down"
    except:
        health_status["status"] = "unhealthy"
        health_status["checks"]["cache"] = "down"

    from django.conf import settings

    if not settings.DEBUG:
        # Disk space check only in production
        import shutil

        disk_usage = shutil.disk_usage("/")
        free_percent = (disk_usage.free / disk_usage.total) * 100
        health_status["checks"]["disk_space"] = {
            "status": "ok" if free_percent > 10 else "critical",
            "free_percent": round(free_percent, 2),
        }

    status_code = 200 if health_status["status"] == "healthy" else 503
    return JsonResponse(health_status, status=status_code)
