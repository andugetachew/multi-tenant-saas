from django.db import models
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from projects.serializers import ProjectSerializer, TaskSerializer
from accounts.permissions import IsAdminOrOwner
from notifications.utils import create_notification
from rest_framework.throttling import UserRateThrottle
from core.throttles import BurstRateThrottle, OrganizationRateThrottle
from .search import ProjectSearch, TaskSearch
from .models import Project
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class ProjectListCreateView(generics.ListCreateAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOwner]

    def get_queryset(self):
        user = self.request.user
        org = user.organization
        if user.role == "admin" or user.is_owner:
            return Project.objects.filter(organization=org)
        else:
            return Project.objects.filter(organization=org, created_by=user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context

    def create(self, request, *args, **kwargs):
        import traceback

        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            print("=" * 60)
            print("ERROR TRACEBACK:")
            traceback.print_exc()
            print("=" * 60)
            return Response(
                {"error": str(e), "trace": traceback.format_exc()},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def perform_create(self, serializer):
        serializer.save(
            organization=self.request.user.organization, created_by=self.request.user
        )


class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOwner]

    def get_queryset(self):
        from projects.models import Project

        user = self.request.user
        org = user.organization

        if user.role == "admin" or user.is_owner:
            return Project.objects.filter(organization=org)
        else:
            return Project.objects.filter(organization=org, created_by=user)


class TaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOwner]

    def get_queryset(self):
        from projects.models import Task

        user = self.request.user
        project_id = self.request.query_params.get("project_id")

        queryset = Task.objects.filter(project__organization=user.organization)

        if project_id:
            queryset = queryset.filter(project_id=project_id)

        if user.role == "viewer":
            queryset = queryset.filter(assigned_to=user)
        elif user.role == "member" and not (user.role == "admin" or user.is_owner):
            queryset = queryset.filter(
                models.Q(created_by=user) | models.Q(assigned_to=user)
            )

        return queryset

    def create(self, request, *args, **kwargs):
        from projects.models import Task

        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Get project and verify it belongs to user's organization
            project_id = request.data.get("project")
            from projects.models import Project

            project = Project.objects.get(
                id=project_id, organization=request.user.organization
            )

            task = Task.objects.create(
                project=project,
                title=request.data.get("title"),
                description=request.data.get("description", ""),
                priority=request.data.get("priority", "medium"),
                status=request.data.get("status", "pending"),
                created_by=request.user,
            )

            return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(f"Error creating task: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        project_id = self.request.data.get("project")
        serializer.save(project_id=project_id, created_by=self.request.user)


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOwner]

    def get_queryset(self):
        from projects.models import Task
        from django.db import models

        user = self.request.user
        queryset = Task.objects.filter(project__organization=user.organization)

        if user.role == "viewer":
            queryset = queryset.filter(assigned_to=user)
        elif user.role == "member" and not (user.role == "admin" or user.is_owner):
            queryset = queryset.filter(
                models.Q(created_by=user) | models.Q(assigned_to=user)
            )

        return queryset


class DashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from projects.models import Project, Task

        user = request.user
        org = user.organization

        if user.role == "admin" or user.is_owner:
            projects = Project.objects.filter(organization=org)
            tasks = Task.objects.filter(project__organization=org)
            users_count = org.users.count()
        else:
            projects = Project.objects.filter(organization=org, created_by=user)
            tasks = Task.objects.filter(
                models.Q(project__organization=org)
                & (models.Q(created_by=user) | models.Q(assigned_to=user))
            )
            users_count = 1

        stats = {
            "organization_name": org.name,
            "organization_plan": org.plan,
            "total_projects": projects.count(),
            "total_tasks": tasks.count(),
            "completed_tasks": tasks.filter(status="completed").count(),
            "pending_tasks": tasks.filter(status="pending").count(),
            "in_progress_tasks": tasks.filter(status="in_progress").count(),
            "total_users": users_count,
            "user_role": user.role,
            "is_owner": user.is_owner,
        }
        return Response(stats)


class ProjectSearchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .models import Project

        query = request.query_params.get("q", "")
        search = ProjectSearch(Project.objects.all(), request.user)
        results = search.search(
            query,
            {
                "status": request.query_params.get("status"),
                "date_from": request.query_params.get("date_from"),
                "date_to": request.query_params.get("date_to"),
            },
        )
        from .serializers import ProjectSerializer

        serializer = ProjectSerializer(results, many=True)
        return Response({"count": results.count(), "results": serializer.data})


class TaskSearchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .models import Task

        query = request.query_params.get("q", "")
        search = TaskSearch(Task.objects.all(), request.user)
        results = search.search(
            query,
            {
                "status": request.query_params.get("status"),
                "priority": request.query_params.get("priority"),
                "assigned_to": request.query_params.get("assigned_to"),
            },
        )
        from .serializers import TaskSerializer

        serializer = TaskSerializer(results, many=True)
        return Response({"count": results.count(), "results": serializer.data})
