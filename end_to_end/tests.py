# end_to_end/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class EndToEndTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_complete_workflow(self):
        # 1. Register new user
        register_data = {
            "email": "e2e@example.com",
            "password": "testpass123",
            "password2": "testpass123",
            "first_name": "E2E",
            "last_name": "Tester",
            "organization_name": "E2E Corp",
        }
        register_response = self.client.post(
            "/api/auth/register/", register_data, format="json"
        )
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)

        # 2. Login
        login_data = {"email": "e2e@example.com", "password": "testpass123"}
        login_response = self.client.post("/api/auth/login/", login_data, format="json")
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        token = login_response.data["access"]

        # Set auth header
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # 3. Create project
        project_data = {"name": "E2E Project", "description": "Testing end to end"}
        project_response = self.client.post(
            "/api/projects/", project_data, format="json"
        )
        self.assertEqual(project_response.status_code, status.HTTP_201_CREATED)
        project_id = project_response.data["id"]

        # 4. Create task
        task_data = {
            "project": project_id,
            "title": "Complete E2E test",
            "priority": "high",
        }
        task_response = self.client.post(
            "/api/projects/tasks/", task_data, format="json"
        )
        self.assertEqual(task_response.status_code, status.HTTP_201_CREATED)

        # 5. Add comment
        comment_data = {"project": project_id, "content": "Working great!"}
        comment_response = self.client.post(
            "/api/comments/", comment_data, format="json"
        )
        self.assertEqual(comment_response.status_code, status.HTTP_201_CREATED)

        # 6. Verify dashboard
        dashboard_response = self.client.get("/api/projects/dashboard/stats/")
        self.assertEqual(dashboard_response.status_code, status.HTTP_200_OK)
        self.assertEqual(dashboard_response.data["total_projects"], 1)
        self.assertEqual(dashboard_response.data["total_tasks"], 1)

        # 7. Export to CSV
        csv_response = self.client.get("/api/projects/export/projects/csv/")
        self.assertEqual(csv_response.status_code, status.HTTP_200_OK)

    def test_multi_tenant_isolation(self):
        # Create two separate users with different orgs
        register1 = self.client.post(
            "/api/auth/register/",
            {
                "email": "tenant1@example.com",
                "password": "pass123",
                "password2": "pass123",
                "organization_name": "Tenant One",
            },
            format="json",
        )

        register2 = self.client.post(
            "/api/auth/register/",
            {
                "email": "tenant2@example.com",
                "password": "pass123",
                "password2": "pass123",
                "organization_name": "Tenant Two",
            },
            format="json",
        )

        # Login as tenant1
        login1 = self.client.post(
            "/api/auth/login/",
            {"email": "tenant1@example.com", "password": "pass123"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {login1.data["access"]}')

        # Create project for tenant1
        self.client.post("/api/projects/", {"name": "Tenant 1 Project"}, format="json")

        # Login as tenant2
        login2 = self.client.post(
            "/api/auth/login/",
            {"email": "tenant2@example.com", "password": "pass123"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {login2.data["access"]}')

        # Tenant2 should NOT see tenant1's project
        projects_response = self.client.get("/api/projects/")
        self.assertEqual(len(projects_response.data), 0)
