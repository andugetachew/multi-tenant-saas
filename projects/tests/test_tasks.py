from django.test import TestCase  # ✅ was commented out
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from organizations.models import Organization
from accounts.models import User
from projects.models import Project, Task


class TaskAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Test Org")
        self.user = User.objects.create_user(
            email="taskuser@example.com",  # ✅ unique, not user@example.com
            password="pass123",
            organization=self.org,
            is_email_verified=True,
            role="admin",  # ✅ admin role so updates are allowed
        )
        self.project = Project.objects.create(
            name="Test Project", organization=self.org, created_by=self.user
        )
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_create_task(self):
        """Test creating a task"""
        url = reverse("task-list")
        data = {
            "project": self.project.id,
            "title": "Test Task",
            "priority": "high",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["title"], "Test Task")

    def test_list_tasks(self):
        """Test listing tasks"""
        Task.objects.create(project=self.project, title="Task 1", created_by=self.user)
        Task.objects.create(project=self.project, title="Task 2", created_by=self.user)

        url = reverse("task-list")
        response = self.client.get(url, {"project_id": self.project.id})
        self.assertEqual(response.status_code, 200)

        # ✅ handle both paginated and non-paginated responses
        if isinstance(response.data, dict) and "results" in response.data:
            tasks = [
                t
                for t in response.data["results"]
                if t["project"] == self.project.id  # ✅ filter to this project only
            ]
        else:
            tasks = [t for t in response.data if t["project"] == self.project.id]

        self.assertEqual(len(tasks), 2)

    def test_update_task_status(self):
        """Test updating task status"""
        task = Task.objects.create(
            project=self.project,
            title="Test Task",
            status="pending",
            created_by=self.user,  # ✅ same user who will update it
        )

        url = reverse("task-detail", kwargs={"pk": task.id})
        data = {"status": "completed"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.status, "completed")
