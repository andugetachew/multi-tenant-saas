# tests/test_integration.py
import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestIntegration:

    def test_full_workflow(self, api_client):
        """Test complete user workflow"""

        # 1. Register
        register_url = reverse("register")
        register_data = {
            "email": "workflow@example.com",
            "password": "SecurePass123!",
            "password2": "SecurePass123!",
            "first_name": "Workflow",
            "last_name": "User",
            "organization_name": "Workflow Org",
        }
        response = api_client.post(register_url, register_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        # 2. Verify email (simulate)
        from accounts.models import User

        user = User.objects.get(email="workflow@example.com")
        token = user.email_verification_token
        verify_url = reverse("verify-email")
        response = api_client.post(verify_url, {"token": token}, format="json")
        assert response.status_code == status.HTTP_200_OK

        # 3. Login
        login_url = reverse("login")
        login_data = {"email": "workflow@example.com", "password": "SecurePass123!"}
        response = api_client.post(login_url, login_data, format="json")
        assert response.status_code == status.HTTP_200_OK
        access_token = response.data["access"]

        # 4. Create project
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        project_url = reverse("project-list")
        project_data = {"name": "Integration Project", "status": "active"}
        response = api_client.post(project_url, project_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        project_id = response.data["id"]

        # 5. Create task
        task_url = reverse("task-list")
        task_data = {
            "project": project_id,
            "title": "Integration Task",
            "priority": "high",
        }
        response = api_client.post(task_url, task_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        # 6. Create comment
        comment_url = reverse("comment-list")
        comment_data = {"project": project_id, "content": "Integration test comment"}
        response = api_client.post(comment_url, comment_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        # 7. Check dashboard
        dashboard_url = reverse("dashboard-stats")
        response = api_client.get(dashboard_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_projects"] >= 1
        assert response.data["total_tasks"] >= 1

        # 8. Search
        search_url = reverse("global-search")
        response = api_client.get(search_url, {"q": "Integration"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]["projects"]) >= 1
