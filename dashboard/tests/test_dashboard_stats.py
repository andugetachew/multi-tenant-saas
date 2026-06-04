from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from organizations.models import Organization
from accounts.models import User
from projects.models import Project, Task


class DashboardStatsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Test Org", plan="basic")
        self.user = User.objects.create_user(
            email="user@example.com",
            password="pass123",
            organization=self.org,
            is_email_verified=True,
            is_owner=True,
        )
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_dashboard_stats(self):
        """Test dashboard statistics endpoint"""
        project = Project.objects.create(
            name="Test Project", organization=self.org, created_by=self.user
        )
        Task.objects.create(
            project=project, title="Test Task", status="pending", created_by=self.user
        )

        url = "/api/projects/dashboard/stats/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_projects"], 1)
        self.assertEqual(response.data["total_tasks"], 1)
        self.assertEqual(response.data["organization_name"], "Test Org")

    def test_dashboard_stats_empty(self):
        """Test dashboard stats with no data"""
        url = "/api/projects/dashboard/stats/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_projects"], 0)
        self.assertEqual(response.data["total_tasks"], 0)
