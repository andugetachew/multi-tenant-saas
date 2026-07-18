import pytest
from unittest.mock import patch
from rest_framework.test import APIRequestFactory, force_authenticate

from organizations.models import Organization
from accounts.models import User
from projects.models import Project, Task
from comments.models import Comment
from dashboard.views import RealTimeDashboardView, DashboardStatsView

factory = APIRequestFactory()


@pytest.fixture
def org(db):
    return Organization.objects.create(name="Acme Corp")


@pytest.fixture
def user(org):
    return User.objects.create_user(email="u@acme.com", password="pass123", organization=org)


@pytest.mark.django_db
class TestRealTimeDashboardView:
    def test_returns_expected_stats(self, user, org):
        project = Project.objects.create(organization=org, name="P1", created_by=user)
        Task.objects.create(project=project, title="T1", status="completed")
        Task.objects.create(project=project, title="T2", status="pending")
        Comment.objects.create(project=project, user=user, content="hi")

        request = factory.get("/api/dashboard/realtime/")
        force_authenticate(request, user=user)
        response = RealTimeDashboardView.as_view()(request)

        assert response.status_code == 200
        assert response.data["total_projects"] == 1
        assert response.data["total_tasks"] == 2
        assert response.data["total_comments"] == 1
        assert response.data["completion_rate"] == 50.0
        assert len(response.data["project_trends"]) == 7

    def test_zero_tasks_gives_zero_completion_rate(self, user, org):
        request = factory.get("/api/dashboard/realtime/")
        force_authenticate(request, user=user)
        response = RealTimeDashboardView.as_view()(request)

        assert response.data["completion_rate"] == 0

    def test_exception_returns_500_with_error_message(self, user):
        request = factory.get("/api/dashboard/realtime/")
        force_authenticate(request, user=user)

        with patch("dashboard.views.Project.objects.filter", side_effect=Exception("db down")):
            response = RealTimeDashboardView.as_view()(request)

        assert response.status_code == 500
        assert "error" in response.data


@pytest.mark.django_db
class TestDashboardStatsView:
    def test_returns_expected_stats(self, user, org):
        project = Project.objects.create(organization=org, name="P1", created_by=user)
        Task.objects.create(project=project, title="T1", status="completed")
        Task.objects.create(project=project, title="T2", status="in_progress")
        Task.objects.create(project=project, title="T3", status="pending")

        request = factory.get("/api/dashboard/stats/")
        force_authenticate(request, user=user)
        response = DashboardStatsView.as_view()(request)

        assert response.status_code == 200
        assert response.data["total_tasks"] == 3
        assert response.data["completed_tasks"] == 1
        assert response.data["in_progress_tasks"] == 1
        assert response.data["pending_tasks"] == 2
        assert response.data["organization_name"] == org.name