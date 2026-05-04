from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Project, Task
from organizations.models import Organization

User = get_user_model()


class ProjectModelTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Test Org")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="pass123",
            organization=self.org,
            role="admin",  # Add role
        )

    def test_create_project(self):
        project = Project.objects.create(
            name="Test Project", organization=self.org, created_by=self.user
        )
        self.assertEqual(project.name, "Test Project")
        self.assertEqual(project.status, "active")

    def test_project_str_method(self):
        project = Project.objects.create(
            name="My Project", organization=self.org, created_by=self.user
        )
        self.assertEqual(str(project), "My Project")


class TaskModelTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Test Org")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="pass123",
            organization=self.org,
            role="admin",
        )
        self.project = Project.objects.create(
            name="Test Project", organization=self.org, created_by=self.user
        )

    def test_create_task(self):
        task = Task.objects.create(
            title="Test Task", project=self.project, created_by=self.user
        )
        self.assertEqual(task.title, "Test Task")
        self.assertEqual(task.status, "pending")

    def test_task_str_method(self):
        task = Task.objects.create(
            title="Complete work", project=self.project, created_by=self.user
        )
        self.assertEqual(str(task), "Complete work")


class ProjectAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Test Org")
        self.user = User.objects.create_user(
            email="api@example.com",
            password="pass123",
            organization=self.org,
            role="admin",
            is_owner=True,
        )
        self.client.force_authenticate(user=self.user)
        self.client.defaults["HTTP_X_ORGANIZATION_ID"] = str(self.org.id)

    def test_create_project(self):
        data = {"name": "API Project", "description": "Test via API"}
        response = self.client.post("/api/projects/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 1)

    def test_list_projects(self):
        Project.objects.create(
            name="Project 1", organization=self.org, created_by=self.user
        )
        Project.objects.create(
            name="Project 2", organization=self.org, created_by=self.user
        )

        response = self.client.get("/api/projects/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_update_project(self):
        project = Project.objects.create(
            name="Original Name", organization=self.org, created_by=self.user
        )
        data = {"name": "Updated Name"}
        response = self.client.put(f"/api/projects/{project.id}/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Name")

    def test_delete_project(self):
        project = Project.objects.create(
            name="To Delete", organization=self.org, created_by=self.user
        )
        response = self.client.delete(f"/api/projects/{project.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Project.objects.count(), 0)

    def test_org_isolation_projects(self):
        Project.objects.create(
            name="User Project", organization=self.org, created_by=self.user
        )

        org2 = Organization.objects.create(name="Org 2")
        user2 = User.objects.create_user(
            email="user2@example.com",
            password="pass123",
            organization=org2,
            role="member",
        )
        Project.objects.create(
            name="Other Project", organization=org2, created_by=user2
        )

        response = self.client.get("/api/projects/")
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "User Project")


class TaskAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Test Org")
        self.user = User.objects.create_user(
            email="task@example.com",
            password="pass123",
            organization=self.org,
            role="admin",
            is_owner=True,
        )
        self.client.force_authenticate(user=self.user)
        self.client.defaults["HTTP_X_ORGANIZATION_ID"] = str(self.org.id)
        self.project = Project.objects.create(
            name="Test Project", organization=self.org, created_by=self.user
        )

    def test_create_task(self):
        data = {"project": self.project.id, "title": "New Task", "priority": "high"}
        response = self.client.post("/api/projects/tasks/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 1)

    def test_list_tasks(self):
        Task.objects.create(title="Task 1", project=self.project, created_by=self.user)
        Task.objects.create(title="Task 2", project=self.project, created_by=self.user)

        response = self.client.get("/api/projects/tasks/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_update_task_status(self):
        task = Task.objects.create(
            title="Complete work",
            project=self.project,
            created_by=self.user,
            status="pending",
        )
        data = {"status": "completed"}
        response = self.client.patch(
            f"/api/projects/tasks/{task.id}/", data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "completed")
