from django.urls import path
from .views import ActivityFeedView, AuditLogListView, AuditLogDetailView

urlpatterns = [
    path("feed/", ActivityFeedView.as_view(), name="activity-feed"),
    path("", AuditLogListView.as_view(), name="audit-log-list"),
    path("<int:pk>/", AuditLogDetailView.as_view(), name="audit-log-detail"),
]
