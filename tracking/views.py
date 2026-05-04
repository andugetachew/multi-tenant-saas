from rest_framework.views import APIView
from rest_framework import generics, permissions
from rest_framework.response import Response
from django.db import models
from .models import TimeEntry
from .serializers import TimeEntrySerializer


class TimeEntryListCreateView(generics.ListCreateAPIView):
    serializer_class = TimeEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TimeEntry.objects.filter(
            task__project__organization=self.request.user.organization
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TimeEntryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TimeEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TimeEntry.objects.filter(
            task__project__organization=self.request.user.organization
        )


class TaskTimeSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, task_id):
        from projects.models import Task

        try:
            task = Task.objects.get(
                id=task_id, project__organization=request.user.organization
            )
            total_hours = (
                task.time_entries.aggregate(total=models.Sum("hours"))["total"] or 0
            )
            return Response(
                {
                    "task_id": task.id,
                    "task_title": task.title,
                    "total_hours": float(total_hours),
                    "status": task.status,
                    "priority": task.priority,
                }
            )
        except Task.DoesNotExist:
            return Response({"error": "Task not found"}, status=404)
