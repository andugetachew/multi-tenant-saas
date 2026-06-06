from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from organizations.models import Organization
from accounts.models import User


class ProjectWorkflowIntegrationTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Test Org")
        self.user = User.objects.create_user(
            email="user@test.com",
            password="pass123",
            organization=self.org,
            is_email_verified=True,
        )
        token = RefreshToken.for_user(self.user).access_token
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_complete_project_task_comment_workflow(self):
        # 1. Create project
        res = self.client.post("/api/projects/", {"name": "Sprint 1"})
        self.assertEqual(res.status_code, 201)
        project_id = res.data["id"]

        # 2. Create task
        res = self.client.post("/api/projects/tasks/", {
            "project": project_id,
            "title": "Implement feature",
            "priority": "high"
        })
        self.assertEqual(res.status_code, 201)
        task_id = res.data["id"]

        # 3. Create comment on project
        res = self.client.post("/api/comments/", {
            "project": project_id,
            "content": "Great progress!"
        })
        self.assertEqual(res.status_code, 201)

        # 4. Get project detail
        res = self.client.get(f"/api/projects/{project_id}/")
        self.assertEqual(res.status_code, 200)

        # 5. Get task detail
        res = self.client.get(f"/api/projects/tasks/{task_id}/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["project"], project_id)

    def test_tenant_safety_during_workflow(self):
        """Ensure workflow never leaks cross-tenant data"""
        other_org = Organization.objects.create(name="Other Org")
        other_user = User.objects.create_user(
            email="other@test.com",
            password="pass123",
            organization=other_org,
            is_email_verified=True,
        )
        other_token = RefreshToken.for_user(other_user).access_token
        other_client = APIClient()
        other_client.credentials(HTTP_AUTHORIZATION=f"Bearer {other_token}")

        res = self.client.post("/api/projects/", {"name": "Private Project"})
        project_id = res.data["id"]

        res = other_client.get(f"/api/projects/{project_id}/")
        self.assertEqual(res.status_code, 404)