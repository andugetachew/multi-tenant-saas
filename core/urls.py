from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from django.conf import settings
from django.conf.urls.static import static
from core.health import health_check
from rest_framework import permissions
from projects.task_comments import TaskCommentView
from projects.templates import ProjectTemplateView
from activity.feed import ActivityFeedView
from reports.views import ComprehensiveReportView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Multi-Tenant SaaS API",
        default_version="v1",
        description="SaaS Platform API",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/organizations/", include("organizations.urls")),
    path("api/projects/", include("projects.urls")),
    path("api/logs/", include("logs.urls")),
    path("api/comments/", include("comments.urls")),
    path("api/notifications/", include("notifications.urls")),
    path("api/webhooks/", include("webhooks.urls")),
    path("api/analytics/", include("analytics.urls")),
    path("api/bulk/", include("projects.bulk_urls")),
    path("api/v1/", include("core.api_v1_urls")),
    path("api/v2/", include("core.api_v2_urls")),
    path("api/tracking/", include("tracking.urls")),
    path("api/audit/", include("audit.urls")),
    path("api/dashboard/", include("dashboard.urls")),
    path("api/ai/", include("ai.urls")),
    path("api/reports/", include("reports.urls")),
    path("api/custom-fields/", include("custom_fields.urls")),
    path("health/", health_check, name="health-check"),
    path(
        "api/tasks/<int:task_id>/comments/",
        TaskCommentView.as_view(),
        name="task-comments",
    ),
    path(
        "api/project-templates/",
        ProjectTemplateView.as_view(),
        name="project-templates",
    ),
    path("api/activity-feed/", ActivityFeedView.as_view(), name="activity-feed"),
    path(
        "api/reports/comprehensive/",
        ComprehensiveReportView.as_view(),
        name="comprehensive-report",
    ),
    path("api/search/", include("projects.search_urls")),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
