from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from datetime import timedelta
from django.utils import timezone
from .models import AnalyticsEvent
from projects.models import Project, Task
from django.db.models import Sum, Count, Q, Avg, F
from datetime import timedelta, datetime
from organizations.models import Organization

from accounts.models import User
from billing.models import Transaction


class DashboardAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = request.user.organization
        now = timezone.now()
        last_30_days = now - timedelta(days=30)

        analytics = {
            "projects": {
                "total": Project.objects.filter(organization=org).count(),
                "created_last_30_days": Project.objects.filter(
                    organization=org, created_at__gte=last_30_days
                ).count(),
            },
            "tasks": {
                "total": Task.objects.filter(project__organization=org).count(),
                "completed": Task.objects.filter(
                    project__organization=org, status="completed"
                ).count(),
                "overdue": Task.objects.filter(
                    project__organization=org,
                    due_date__lt=now,
                    status__in=["pending", "in_progress"],
                ).count(),
            },
            "activity": {
                "total_events": AnalyticsEvent.objects.filter(
                    organization=org, created_at__gte=last_30_days
                ).count(),
                "by_type": dict(
                    AnalyticsEvent.objects.filter(
                        organization=org, created_at__gte=last_30_days
                    )
                    .values_list("event_type")
                    .annotate(count=Count("id"))
                ),
            },
        }
        return Response(analytics)


class RevenueAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = request.user.organization

        if not request.user.is_owner and request.user.role != "admin":
            return Response({"error": "Permission denied"}, status=403)

        # Get revenue data for last 12 months
        now = timezone.now()
        revenue_data = []
        total_revenue = 0

        for i in range(12):
            month_start = now.replace(day=1) - timedelta(days=30 * i)
            month_start = month_start.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )

            if i == 0:
                month_end = now
            else:
                month_end = (month_start + timedelta(days=32)).replace(
                    day=1
                ) - timedelta(days=1)

            # Calculate revenue for this month
            monthly_revenue = (
                Transaction.objects.filter(
                    organization=org,
                    status="completed",
                    created_at__range=[month_start, month_end],
                ).aggregate(total=Sum("amount"))["total"]
                or 0
            )

            total_revenue += monthly_revenue

            revenue_data.append(
                {
                    "month": month_start.strftime("%B %Y"),
                    "revenue": float(monthly_revenue),
                    "subscriptions": Transaction.objects.filter(
                        organization=org,
                        type="subscription",
                        created_at__range=[month_start, month_end],
                    ).count(),
                }
            )

        # Calculate growth rate
        growth_rate = "0%"
        if len(revenue_data) >= 2:
            prev_revenue = revenue_data[1]["revenue"]
            current_revenue = revenue_data[0]["revenue"]
            if prev_revenue > 0:
                growth = ((current_revenue - prev_revenue) / prev_revenue) * 100
                growth_rate = f"{growth:+.1f}%"

        return Response(
            {
                "revenue": revenue_data,
                "total_revenue": float(total_revenue),
                "growth_rate": growth_rate,
                "currency": "USD",
            }
        )


class SellerPerformanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = request.user.organization

        if not request.user.is_owner and request.user.role != "admin":
            return Response({"error": "Permission denied"}, status=403)

        performance_data = []

        for user in org.users.all():
            tasks_assigned = Task.objects.filter(
                assigned_to=user, project__organization=org
            ).count()

            tasks_completed = Task.objects.filter(
                assigned_to=user, status="completed", project__organization=org
            ).count()

            tasks_in_progress = Task.objects.filter(
                assigned_to=user, status="in_progress", project__organization=org
            ).count()

            # Calculate average completion time
            completed_tasks = Task.objects.filter(
                assigned_to=user,
                status="completed",
                completed_at__isnull=False,
                project__organization=org,
            )

            avg_completion_hours = 0
            for task in completed_tasks:
                if task.created_at and task.completed_at:
                    diff = (task.completed_at - task.created_at).total_seconds() / 3600
                    if diff > 0:
                        avg_completion_hours += diff

            avg_completion_hours = (
                avg_completion_hours / len(completed_tasks) if completed_tasks else 0
            )

            completion_rate = (
                (tasks_completed / tasks_assigned * 100) if tasks_assigned > 0 else 0
            )

            # Calculate performance score
            performance_score = (
                (tasks_completed * 10)
                + (completion_rate * 0.5)
                - (avg_completion_hours * 0.1)
            )

            performance_data.append(
                {
                    "user_id": user.id,
                    "user_email": user.email,
                    "user_name": user.get_full_name(),
                    "role": user.role,
                    "tasks_assigned": tasks_assigned,
                    "tasks_completed": tasks_completed,
                    "tasks_in_progress": tasks_in_progress,
                    "completion_rate": round(completion_rate, 1),
                    "avg_completion_hours": round(avg_completion_hours, 1),
                    "performance_score": round(performance_score, 2),
                }
            )

        # Sort by performance score
        performance_data.sort(key=lambda x: x["performance_score"], reverse=True)

        return Response(
            {
                "top_performers": performance_data[:5],
                "all_performers": performance_data,
                "team_average_completion": (
                    round(
                        sum(p["completion_rate"] for p in performance_data)
                        / len(performance_data),
                        1,
                    )
                    if performance_data
                    else 0
                ),
            }
        )


class SystemHealthView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_superuser:
            return Response({"error": "Admin access required"}, status=403)

        from django.db import connection
        from django.core.cache import cache
        import redis

        # Database health
        db_healthy = False
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                db_healthy = cursor.fetchone()
            db_healthy = True
        except:
            db_healthy = False

        # Cache health
        cache_healthy = False
        try:
            cache.set("health_check", "ok", 10)
            cache_healthy = cache.get("health_check") == "ok"
        except:
            cache_healthy = False

        return Response(
            {
                "status": "healthy" if db_healthy and cache_healthy else "degraded",
                "database": "connected" if db_healthy else "disconnected",
                "cache": "connected" if cache_healthy else "disconnected",
                "timestamp": timezone.now().isoformat(),
            }
        )
