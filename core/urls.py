from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from django.conf import settings
from django.conf.urls.static import static
from core.health import health_check
from projects.task_comments import TaskCommentView
from projects.templates import ProjectTemplateView
from activity.feed import ActivityFeedView
from reports.views import ComprehensiveReportView

from rest_framework_simplejwt.views import TokenRefreshView
from search import urls as search_urls
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(url="/api/docs/"), name="root"),
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/organizations/", include("organizations.urls")),
    path("api/projects/", include("projects.urls")),
    path("api/logs/", include("logs.urls")),
    path("api/comments/", include("comments.urls")),
    path("api/notifications/", include("notifications.urls")),
    path("api/webhooks/", include("webhooks.urls")),
    path("api/analytics/", include("analytics.urls")),
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
    path("api/search/", include("search.urls")),
    path(
        "api/auth/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/billing/", include("billing.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
