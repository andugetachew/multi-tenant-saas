from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from organizations.models import Organization
from accounts.models import User
from projects.models import Project


class TenantIsolationTestCase(TestCase):

    def setUp(self):
        self.org1 = Organization.objects.create(name="Org 1")
        self.org2 = Organization.objects.create(name="Org 2")

        self.user1 = User.objects.create_user(
            email="user1@example.com",
            password="pass123",
            organization=self.org1,
            is_email_verified=True,
        )

        self.user2 = User.objects.create_user(
            email="user2@example.com",
            password="pass123",
            organization=self.org2,
            is_email_verified=True,
        )

        # Projects
        self.project1 = Project.objects.create(
            name="Org1 Project",
            organization=self.org1,
            created_by=self.user1
        )

        self.project2 = Project.objects.create(
            name="Org2 Project",
            organization=self.org2,
            created_by=self.user2
        )

    def _auth_client(self, user):
        token = RefreshToken.for_user(user).access_token
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return client

    def test_user_sees_only_their_organization_projects(self):
        client = self._auth_client(self.user1)

        response = client.get("/api/projects/")
        self.assertEqual(response.status_code, 200)

        # Normalize response (works with or without pagination)
        data = response.data
        projects = data["results"] if isinstance(data, dict) and "results" in data else data

        project_names = [p["name"] for p in projects]

        self.assertIn("Org1 Project", project_names)
        self.assertNotIn("Org2 Project", project_names)

    def test_user_cannot_access_other_org_project_detail(self):
        client = self._auth_client(self.user1)

        response = client.get(f"/api/projects/{self.project2.id}/")

        self.assertEqual(response.status_code, 404)

    def test_user_cannot_update_other_org_project(self):
        client = self._auth_client(self.user1)

        response = client.patch(
            f"/api/projects/{self.project2.id}/",
            {"name": "Hacked Name"},
            format="json"
        )

        self.assertEqual(response.status_code, 404)

    def test_user_cannot_delete_other_org_project(self):
        client = self._auth_client(self.user1)

        response = client.delete(f"/api/projects/{self.project2.id}/")

        self.assertEqual(response.status_code, 404)

    def test_user_cannot_assign_project_to_other_org(self):
        client = self._auth_client(self.user1)

        response = client.post("/api/projects/", {
            "name": "Malicious Project",
            "organization": self.org2.id
        })

        self.assertEqual(response.status_code, 201)

        # MUST be forced into user's org (critical SaaS rule)
        self.assertEqual(response.data["organization"], self.org1.id)

    def test_database_level_isolation(self):
        """Extra safety: ensures DB query isolation works correctly"""
        self.assertEqual(Project.objects.filter(organization=self.org1).count(), 1)
        self.assertEqual(Project.objects.filter(organization=self.org2).count(), 1)