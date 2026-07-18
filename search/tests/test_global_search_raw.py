import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from organizations.models import Organization
from accounts.models import User
from projects.models import Project, Task
from comments.models import Comment
from search.views import GlobalSearchView

factory = APIRequestFactory()


@pytest.fixture
def org(db):
    return Organization.objects.create(name="Acme Corp")


@pytest.fixture
def user(org):
    return User.objects.create_user(email="u@acme.com", password="pass123", organization=org)


@pytest.mark.django_db
class TestGlobalSearchView:
    def test_empty_query_returns_400(self, user):
        request = factory.get("/api/search/", {"q": ""})
        force_authenticate(request, user=user)

        view = GlobalSearchView.as_view()
        response = view(request)

        assert response.status_code == 400

    def test_no_organization_returns_400(self):
        user = User.objects.create(email="noorg@test.com")
        user.set_password("pass123")
        user.organization = None
        user.save()

        request = factory.get("/api/search/", {"q": "test"})
        force_authenticate(request, user=user)

        view = GlobalSearchView.as_view()
        response = view(request)

        assert response.status_code == 400

    def test_finds_projects_tasks_and_comments(self, user, org):
        project = Project.objects.create(organization=org, name="dashboard redesign", created_by=user)
        Task.objects.create(project=project, title="dashboard bugfix")
        Comment.objects.create(project=project, user=user, content="dashboard looks good")

        request = factory.get("/api/search/", {"q": "dashboard"})
        force_authenticate(request, user=user)

        view = GlobalSearchView.as_view()
        response = view(request)

        assert response.status_code == 200
        assert len(response.data["results"]["projects"]) == 1
        assert len(response.data["results"]["tasks"]) == 1
        assert len(response.data["results"]["comments"]) == 1

    def test_no_results_returns_empty_lists(self, user, org):
        request = factory.get("/api/search/", {"q": "nonexistent_xyz"})
        force_authenticate(request, user=user)

        view = GlobalSearchView.as_view()
        response = view(request)

        assert response.data["results"]["projects"] == []
        assert response.data["results"]["tasks"] == []