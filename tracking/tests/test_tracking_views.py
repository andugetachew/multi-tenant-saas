import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from organizations.models import Organization
from accounts.models import User
from projects.models import Project, Task
from tracking.models import TimeEntry
from tracking.views import TimeEntryListCreateView, TimeEntryDetailView, TaskTimeSummaryView

factory = APIRequestFactory()


@pytest.fixture
def org(db):
    return Organization.objects.create(name="Acme Corp")


@pytest.fixture
def user(org):
    return User.objects.create_user(email="u@acme.com", password="pass123", organization=org)


@pytest.fixture
def project(org, user):
    return Project.objects.create(organization=org, name="P1", created_by=user)


@pytest.fixture
def task(project):
    return Task.objects.create(project=project, title="T1")


@pytest.mark.django_db
class TestTimeEntryListCreateView:
    def test_creates_entry_with_authenticated_user(self, user, task):
        request = factory.post(
            "/api/time-entries/", {"task": task.id, "hours": "2.5"}, format="json"
        )
        force_authenticate(request, user=user)

        view = TimeEntryListCreateView.as_view()
        response = view(request)

        assert response.status_code == 201
        entry = TimeEntry.objects.get(task=task)
        assert entry.user == user
        assert float(entry.hours) == 2.5

    def test_only_lists_own_organization_entries(self, user, task):
        other_org = Organization.objects.create(name="Other")
        other_user = User.objects.create_user(
            email="other@test.com", password="pass123", organization=other_org
        )
        other_project = Project.objects.create(
            organization=other_org, name="OtherP", created_by=other_user
        )
        other_task = Task.objects.create(project=other_project, title="OtherT")

        TimeEntry.objects.create(task=task, user=user, hours=1)
        TimeEntry.objects.create(task=other_task, user=other_user, hours=2)

        request = factory.get("/api/time-entries/")
        force_authenticate(request, user=user)

        view = TimeEntryListCreateView.as_view()
        response = view(request)

        assert len(response.data["results"]) == 1


@pytest.mark.django_db
class TestTaskTimeSummaryView:
    def test_returns_total_hours_for_task(self, user, task):
        TimeEntry.objects.create(task=task, user=user, hours=2)
        TimeEntry.objects.create(task=task, user=user, hours=3)

        request = factory.get("/api/time-summary/")
        force_authenticate(request, user=user)

        view = TaskTimeSummaryView.as_view()
        response = view(request, task_id=task.id)

        assert response.status_code == 200
        assert response.data["total_hours"] == 5.0

    def test_task_not_found_returns_404(self, user):
        request = factory.get("/api/time-summary/")
        force_authenticate(request, user=user)

        view = TaskTimeSummaryView.as_view()
        response = view(request, task_id=99999)

        assert response.status_code == 404