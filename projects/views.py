from django.db import models
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import UserRateThrottle
from rest_framework.exceptions import PermissionDenied
from projects.serializers import ProjectSerializer, TaskSerializer
from accounts.permissions import IsAdminOrOwner
from notifications.utils import create_notification
from core.throttles import BurstRateThrottle, OrganizationRateThrottle
from organizations.limits import check_org_limit, get_remaining_limit
from .search import ProjectSearch, TaskSearch
from .models import Project, Task
import logging
from django.utils import timezone
from core.pagination import StandardPagination, CursorPagination
from core.permissions import IsOrganizationMember, IsOwnerOrAdmin
from core.rate_limits import ProjectCreateThrottle, TaskCreateThrottle
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

class ProjectListCreateView(generics.ListCreateAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOwner]
    throttle_classes = [BurstRateThrottle, OrganizationRateThrottle]
    pagination_class = StandardPagination

    def get_throttles(self):
        if self.request.method == "POST":
            self.throttle_classes = [ProjectCreateThrottle]
        else:
            self.throttle_classes = []
        return super().get_throttles()

    def get_queryset(self):
        user = self.request.user
        org = user.organization

        if not org:
            return Project.objects.none()

        queryset = Project.objects.filter(organization=org).select_related(
            "organization", "created_by"
        )

       
        if user.role == "admin" or user.is_owner:
            return queryset
        elif user.role == "member":
         
            return queryset.filter(created_by=user)
        elif user.role == "viewer":

            return queryset
        
        return Project.objects.none()

    def create(self, request, *args, **kwargs):
        import traceback

        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Project creation error: {str(e)}")
            traceback.print_exc()
            return Response(
                {"error": str(e), "trace": traceback.format_exc()},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def perform_create(self, serializer):
        org = self.request.user.organization

        if not org:
            from organizations.models import Organization

            org = Organization.objects.create(
                name=f"{self.request.user.email}'s Company", plan="trial"
            )
            self.request.user.organization = org
            self.request.user.is_owner = True
            self.request.user.save()

        if not check_org_limit(org, "projects"):
            remaining = get_remaining_limit(org, "projects")
            raise PermissionDenied(
                f"Project limit reached. You can create {remaining} more projects."
            )

        project = serializer.save(organization=org, created_by=self.request.user)

        create_notification(
            user=self.request.user,
            title="Project Created",
            message=f"Project '{project.name}' was created successfully",
            notification_type="success",
            link=f"/projects/{project.id}",
        )


class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        org = user.organization

        if not org:
            return Project.objects.none()

        return Project.objects.filter(organization=org).select_related(
            "organization", "created_by"
        )

    def get_object(self):
        obj = super().get_object()
        user = self.request.user

        if self.request.method not in ("GET", "HEAD", "OPTIONS"):
            if user.role == "viewer":
                raise PermissionDenied("Viewers have read-only access")
            if user.role == "member" and not user.is_owner and obj.created_by != user:
                raise PermissionDenied("You do not have permission to access this project")

        return obj

    def destroy(self, request, *args, **kwargs):
        """Allow members to delete their own projects"""
        instance = self.get_object()
        user = request.user

        if user.role == "member" and not user.is_owner:
            if instance.created_by != user:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You cannot delete this project")
        
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOwner]
    throttle_classes = [BurstRateThrottle, OrganizationRateThrottle]

    def get_throttles(self):
        if self.request.method == "POST":
            self.throttle_classes = [TaskCreateThrottle]
        else:
            self.throttle_classes = []
        return super().get_throttles()

    def get_queryset(self):
        user = self.request.user
        project_id = self.request.query_params.get("project_id")

        queryset = (
            Task.objects.filter(project__organization=user.organization)
            .select_related("project", "assigned_to", "created_by")
            .order_by("-created_at")
        )

        if project_id:
            queryset = queryset.filter(project_id=project_id)

        if user.role == "member" and not (user.role == "admin" or user.is_owner):
            queryset = queryset.filter(
                models.Q(created_by=user) | models.Q(assigned_to=user)
            )
        elif user.role == "viewer":
            queryset = queryset.filter(assigned_to=user)

        return queryset

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            project_id = request.data.get("project")
            user = request.user

            project = Project.objects.get(
                id=project_id, organization=user.organization
            )

            if user.role == "member" and not user.is_owner:
                if project.created_by != user:
                    return Response(
                        {"error": "Project not found or access denied"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

            task = Task.objects.create(
                project=project,
                title=request.data.get("title"),
                description=request.data.get("description", ""),
                priority=request.data.get("priority", "medium"),
                status=request.data.get("status", "pending"),
                created_by=user,
                assigned_to=request.data.get("assigned_to"),
                due_date=request.data.get("due_date"),
                estimated_hours=request.data.get("estimated_hours"),
            )

            return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)

        except Project.DoesNotExist:
            return Response(
                {"error": "Project not found or access denied"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            logger.error(f"Task creation error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        task = serializer.save(created_by=self.request.user)

        create_notification(
            user=self.request.user,
            title="Task Created",
            message=f"Task '{task.title}' was added to project {task.project.name}",
            notification_type="info",
            link=f"/tasks/{task.id}",
        )


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOwner]

    def get_queryset(self):
        user = self.request.user
        queryset = Task.objects.filter(
            project__organization=user.organization
        ).select_related("project", "assigned_to", "created_by")

        if user.role == "member" and not (user.role == "admin" or user.is_owner):
            queryset = queryset.filter(
                models.Q(created_by=user) | models.Q(assigned_to=user)
            )
        elif user.role == "viewer":
            queryset = queryset.filter(assigned_to=user)

        return queryset

    def destroy(self, request, *args, **kwargs):
        """Allow members to delete tasks they created or are assigned to"""
        instance = self.get_object()
        user = request.user
        

        if user.role == "member" and not user.is_owner:
            if instance.created_by != user and instance.assigned_to != user:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You cannot delete this task")
        
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get(self, request):
        user = request.user
        org = user.organization

        if not org:
            return Response(
                {
                    "organization_name": None,
                    "organization_plan": None,
                    "total_projects": 0,
                    "total_tasks": 0,
                    "completed_tasks": 0,
                    "pending_tasks": 0,
                    "in_progress_tasks": 0,
                    "total_users": 0,
                    "user_role": user.role,
                    "is_owner": user.is_owner,
                }
            )

        if user.role == "admin" or user.is_owner:
            projects = Project.objects.filter(organization=org)
            tasks = Task.objects.filter(project__organization=org)
            users_count = org.users.count()
        elif user.role == "member":
            projects = Project.objects.filter(organization=org, created_by=user)
            tasks = Task.objects.filter(
                models.Q(created_by=user) | models.Q(assigned_to=user),
                project__organization=org
            )
            users_count = 1
        else:  
            projects = Project.objects.filter(organization=org)
            tasks = Task.objects.filter(assigned_to=user, project__organization=org)
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
    throttle_classes = [UserRateThrottle]

    def get(self, request):
        query = request.query_params.get("q", "")

        if not query:
            return Response(
                {"error": "Search query required"}, status=status.HTTP_400_BAD_REQUEST
            )

        search = ProjectSearch(Project.objects.all(), request.user)
        results = search.search(
            query,
            {
                "status": request.query_params.get("status"),
                "date_from": request.query_params.get("date_from"),
                "date_to": request.query_params.get("date_to"),
            },
        )
        serializer = ProjectSerializer(results, many=True)
        return Response({"count": results.count(), "results": serializer.data})


class TaskSearchView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get(self, request):
        query = request.query_params.get("q", "")

        if not query:
            return Response(
                {"error": "Search query required"}, status=status.HTTP_400_BAD_REQUEST
            )

        search = TaskSearch(Task.objects.all(), request.user)
        results = search.search(
            query,
            {
                "status": request.query_params.get("status"),
                "priority": request.query_params.get("priority"),
                "assigned_to": request.query_params.get("assigned_to"),
            },
        )
        serializer = TaskSerializer(results, many=True)
        return Response({"count": results.count(), "results": serializer.data})


class BulkProjectDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOwner]

    def post(self, request):
        project_ids = request.data.get("project_ids", [])

        if not project_ids:
            return Response(
                {"error": "No project IDs provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        deleted = Project.objects.filter(
            id__in=project_ids, organization=request.user.organization
        ).delete()

        return Response({"deleted_count": deleted[0]})


class BulkTaskUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        task_ids = request.data.get("task_ids", [])
        updates = request.data.get("updates", {})

        if not task_ids:
            return Response(
                {"error": "No task IDs provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        updated = Task.objects.filter(
            id__in=task_ids, project__organization=request.user.organization
        ).update(**updates)

        return Response({"updated_count": updated})


class BulkProjectArchiveView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOwner]

    def post(self, request):
        project_ids = request.data.get("project_ids", [])

        if not project_ids:
            return Response(
                {"error": "No project IDs provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        updated = Project.objects.filter(
            id__in=project_ids, organization=request.user.organization
        ).update(status="archived")

        return Response({"archived_count": updated})


class TaskAttachmentUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, task_id):
        try:
            task = Task.objects.get(
                id=task_id, project__organization=request.user.organization
            )
        except Task.DoesNotExist:
            return Response(
                {"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND
            )

        file = request.FILES.get("file")
        if not file:
            return Response(
                {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        from .models import TaskAttachment

        attachment = TaskAttachment.objects.create(
            task=task,
            file=file,
            filename=file.name,
            file_size=file.size,
            uploaded_by=request.user,
        )

        return Response(
            {
                "id": attachment.id,
                "filename": attachment.filename,
                "file_size": attachment.file_size,
                "url": attachment.file.url,
            },
            status=status.HTTP_201_CREATED,
        )


class TaskAttachmentListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, task_id):
        try:
            task = Task.objects.get(
                id=task_id, project__organization=request.user.organization
            )
        except Task.DoesNotExist:
            return Response(
                {"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND
            )

        attachments = task.attachments.all()
        return Response(
            [
                {
                    "id": a.id,
                    "filename": a.filename,
                    "file_size": a.file_size,
                    "uploaded_by": a.uploaded_by.email,
                    "created_at": a.created_at,
                }
                for a in attachments
            ]
        )


class RecurringTaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOwner]

    def get_queryset(self):
        from .models import RecurringTask

        return RecurringTask.objects.filter(
            project__organization=self.request.user.organization
        )

    def perform_create(self, serializer):
        serializer.save()

    def create(self, request, *args, **kwargs):
        from .models import RecurringTask
        from .serializers import TaskSerializer as RecurringTaskSerializer

        serializer = RecurringTaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        task = Task.objects.create(
            project_id=request.data.get("project"),
            title=request.data.get("title"),
            description=request.data.get("description", ""),
            priority=request.data.get("priority", "medium"),
            created_by=request.user,
            due_date=request.data.get("next_due_date"),
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TaskTemplateListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        from .models import TaskTemplate

        return TaskTemplate.objects.filter(organization=self.request.user.organization)

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)


class TaskTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        from .models import TaskTemplate

        return TaskTemplate.objects.filter(organization=self.request.user.organization)