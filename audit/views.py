from rest_framework import generics, permissions
from rest_framework.response import Response
from core.pagination import CursorPagination
from .models import ActivityLog

from .serializers import ActivityLogSerializer


class ActivityFeedView(generics.ListAPIView):
    """Activity feed with cursor pagination for infinite scroll"""

    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CursorPagination

    def get_queryset(self):
        user = self.request.user
        if user.is_owner or user.role == "admin":
            return ActivityLog.objects.filter(organization=user.organization)
        return ActivityLog.objects.filter(organization=user.organization, user=user)


class AuditLogListView(generics.ListAPIView):
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_owner or user.role == "admin":
            return ActivityLog.objects.filter(organization=user.organization)
        return ActivityLog.objects.filter(organization=user.organization, user=user)


class AuditLogDetailView(generics.RetrieveAPIView):
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ActivityLog.objects.filter(organization=self.request.user.organization)
