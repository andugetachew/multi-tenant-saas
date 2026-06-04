from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from organizations.models import Organization
from accounts.models import User
from projects.models import Project


class ProjectPermissionsTestCase(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Test Org")

        self.admin_user = User.objects.create_user(
            email="projadmin@example.com",  # ✅ unique, not admin@example.com
            password="pass123",
            organization=self.org,
            role="admin",
            is_email_verified=True,
        )

        self.member_user = User.objects.create_user(
            email="projmember@example.com",  # ✅ unique
            password="pass123",
            organization=self.org,
            role="member",
            is_email_verified=True,
        )

        self.project = Project.objects.create(
            name="Test Project",
            organization=self.org,
            created_by=self.admin_user,
        )

    def test_admin_can_update_any_project(self):
        """Test admin can update any project"""
        refresh = RefreshToken.for_user(self.admin_user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = client.patch(
            f"/api/projects/{self.project.id}/",
            {"name": "Updated by Admin"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

    def test_member_cannot_update_others_project(self):
        """Test member cannot update project created by others"""
        refresh = RefreshToken.for_user(self.member_user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        response = client.patch(
            f"/api/projects/{self.project.id}/",
            {"name": "Updated by Member"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
