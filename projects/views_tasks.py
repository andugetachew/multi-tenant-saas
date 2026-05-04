from rest_framework import generics, permissions
from .models import Task
from .serializers import TaskSerializer
from accounts.permissions import IsAdminOrOwner


class TaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOwner]

    def get_queryset(self):
        project_id = self.request.query_params.get("project_id")
        queryset = Task.objects.filter(
            project__organization=self.request.user.organization
        )
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset

    def perform_create(self, serializer):
        project_id = self.request.data.get("project")
        serializer.save(project_id=project_id, created_by=self.request.user)


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOwner]

    def get_queryset(self):
        return Task.objects.filter(project__organization=self.request.user.organization)
