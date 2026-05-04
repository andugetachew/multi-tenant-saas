from rest_framework import generics, permissions
from rest_framework.response import Response
from .models import ActivityLog
from .serializers import ActivityLogSerializer


class ActivityLogListView(generics.ListAPIView):
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_owner or user.role == "admin":
            return ActivityLog.objects.filter(organization=user.organization)
        else:
            return ActivityLog.objects.filter(organization=user.organization, user=user)


class ActivityLogDetailView(generics.RetrieveAPIView):
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ActivityLog.objects.filter(organization=self.request.user.organization)
