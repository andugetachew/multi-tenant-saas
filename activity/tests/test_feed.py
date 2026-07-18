import pytest
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from organizations.models import Organization
from accounts.models import User
from projects.models import Project, Task
from comments.models import Comment
from activity.feed import ActivityFeedView

factory = APIRequestFactory()


@pytest.fixture
def org(db):
    return Organization.objects.create(name="Acme Corp")


@pytest.fixture
def user(org):
    return User.objects.create_user(email="u@acme.com", password="pass123", organization=org)


@pytest.mark.django_db
class TestActivityFeedView:
    def test_includes_recently_created_project(self, user, org):
        Project.objects.create(organization=org, name="New Project", created_by=user)

        request = factory.get("/api/activity-feed/")
        force_authenticate(request, user=user)
        response = ActivityFeedView.as_view()(request)

        assert response.status_code == 200
        types = [a["type"] for a in response.data["activities"]]
        assert "project_created" in types

    def test_includes_recently_created_task(self, user, org):
        project = Project.objects.create(organization=org, name="P1", created_by=user)
        Task.objects.create(project=project, title="New Task", created_by=user)

        request = factory.get("/api/activity-feed/")
        force_authenticate(request, user=user)
        response = ActivityFeedView.as_view()(request)

        types = [a["type"] for a in response.data["activities"]]
        assert "task_created" in types

    def test_includes_completed_task_with_completed_at(self, user, org):
        project = Project.objects.create(organization=org, name="P1", created_by=user)
        Task.objects.create(
            project=project, title="Done Task", status="completed",
            completed_at=timezone.now(), created_by=user,
        )

        request = factory.get("/api/activity-feed/")
        force_authenticate(request, user=user)
        response = ActivityFeedView.as_view()(request)

        types = [a["type"] for a in response.data["activities"]]
        assert "task_completed" in types

    def test_excludes_completed_task_without_completed_at(self, user, org):
        """A task marked completed but with no completed_at timestamp
        should not show up in the completed-tasks section."""
        project = Project.objects.create(organization=org, name="P1", created_by=user)
        Task.objects.create(project=project, title="No timestamp", status="completed", created_by=user)

        request = factory.get("/api/activity-feed/")
        force_authenticate(request, user=user)
        response = ActivityFeedView.as_view()(request)

        completed_titles = [
            a["title"] for a in response.data["activities"] if a["type"] == "task_completed"
        ]
        assert not any("No timestamp" in t for t in completed_titles)

    def test_includes_comment_with_truncated_content(self, user, org):
        project = Project.objects.create(organization=org, name="P1", created_by=user)
        long_content = "x" * 200
        Comment.objects.create(project=project, user=user, content=long_content)

        request = factory.get("/api/activity-feed/")
        force_authenticate(request, user=user)
        response = ActivityFeedView.as_view()(request)

        comment_activity = next(
            a for a in response.data["activities"] if a["type"] == "comment_added"
        )
        assert len(comment_activity["content"]) == 100

    def test_activities_sorted_by_timestamp_descending(self, user, org):
        project = Project.objects.create(organization=org, name="P1", created_by=user)
        Task.objects.create(project=project, title="Older", created_by=user)
        Task.objects.create(project=project, title="Newer", created_by=user)

        request = factory.get("/api/activity-feed/")
        force_authenticate(request, user=user)
        response = ActivityFeedView.as_view()(request)

        timestamps = [a["timestamp"] for a in response.data["activities"]]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_respects_limit_query_param(self, user, org):
        project = Project.objects.create(organization=org, name="P1", created_by=user)
        for i in range(5):
            Task.objects.create(project=project, title=f"Task {i}", created_by=user)

        request = factory.get("/api/activity-feed/", {"limit": 2})
        force_authenticate(request, user=user)
        response = ActivityFeedView.as_view()(request)

        assert response.data["total"] <= 2
        assert len(response.data["activities"]) <= 2

    def test_shows_system_for_project_with_no_creator(self, user, org):
        project = Project.objects.create(organization=org, name="No Creator")
        project.created_by = None
        project.save()

        request = factory.get("/api/activity-feed/")
        force_authenticate(request, user=user)
        response = ActivityFeedView.as_view()(request)

        project_activity = next(
            a for a in response.data["activities"] if a["type"] == "project_created"
        )
        assert project_activity["user"] == "System"

    def test_only_includes_own_organization_activity(self, user, org):
        other_org = Organization.objects.create(name="Other")
        other_user = User.objects.create_user(
            email="other@test.com", password="pass123", organization=other_org
        )
        Project.objects.create(organization=other_org, name="Not Mine", created_by=other_user)

        request = factory.get("/api/activity-feed/")
        force_authenticate(request, user=user)
        response = ActivityFeedView.as_view()(request)

        titles = [a["title"] for a in response.data["activities"]]
        assert not any("Not Mine" in t for t in titles)