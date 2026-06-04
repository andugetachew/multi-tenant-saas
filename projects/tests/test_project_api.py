from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from organizations.models import Organization
from accounts.models import User
from projects.models import Project


class ProjectAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Test Org", plan="basic")
        self.user = User.objects.create_user(
            email="projectapi_user@example.com",  # ✅ unique email
            password="pass123",
            organization=self.org,
            is_email_verified=True,
            role="admin",
        )
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_create_project(self):
        """Test creating a project"""
        url = reverse("project-list")
        data = {"name": "New Project", "description": "Test description"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "New Project")
        self.assertEqual(response.data["organization"], self.org.id)

    def test_list_projects(self):
        """Test listing projects"""
        Project.objects.create(
            name="Test Project 1", organization=self.org, created_by=self.user
        )
        Project.objects.create(
            name="Test Project 2", organization=self.org, created_by=self.user
        )
        url = reverse("project-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # ✅ filter by this test's org to avoid post_migrate bleed
        results = [
            p for p in response.data["results"] if p["organization"] == self.org.id
        ]
        self.assertEqual(len(results), 2)

    def test_get_project_detail(self):
        """Test getting project details"""
        project = Project.objects.create(
            name="Detail Project", organization=self.org, created_by=self.user
        )
        url = reverse("project-detail", kwargs={"pk": project.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Detail Project")

    def test_update_project(self):
        """Test updating a project"""
        project = Project.objects.create(
            name="Original Name", organization=self.org, created_by=self.user
        )
        url = reverse("project-detail", kwargs={"pk": project.id})
        data = {"name": "Updated Name"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        project.refresh_from_db()
        self.assertEqual(project.name, "Updated Name")

    def test_delete_project(self):
        """Test deleting a project"""
        project = Project.objects.create(
            name="To Delete", organization=self.org, created_by=self.user
        )
        url = reverse("project-detail", kwargs={"pk": project.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Project.objects.filter(id=project.id).exists())
