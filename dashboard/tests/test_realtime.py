from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from organizations.models import Organization
from accounts.models import User


class RealtimeDashboardTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Test Org")
        self.user = User.objects.create_user(
            email="user@example.com",
            password="pass123",
            organization=self.org,
            is_email_verified=True,
        )
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_realtime_dashboard(self):
        """Test real-time dashboard endpoint"""
        url = "/api/dashboard/realtime/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("project_trends", response.data)
        self.assertIn("completion_rate", response.data)
        self.assertIn("active_users", response.data)
        self.assertIn("total_projects", response.data)
