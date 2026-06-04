# core/admin_views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from .rate_limit_monitor import rate_limit_monitor


class RateLimitAdminView(APIView):
    """Admin view to monitor rate limiting"""

    permission_classes = [IsAdminUser]

    def get(self, request):
        date = request.query_params.get("date")
        summary = rate_limit_monitor.get_violations_summary(date)

        return Response(
            {
                "status": "ok",
                "summary": summary,
                "message": "Rate limiting active. Alert threshold: 10 violations/IP",
            }
        )
