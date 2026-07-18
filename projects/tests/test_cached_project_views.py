import pytest
from django.core.cache import cache
from rest_framework.test import APIRequestFactory, force_authenticate

from organizations.models import Organization
from accounts.models import User
from projects.models import Project
from projects.cached_views import CachedProjectListView, CachedProjectCreateView

factory = APIRequestFactory()


@pytest.fixture(autouse=True)
def clean_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def org(db):
    return Organization.objects.create(name="Acme Corp")


@pytest.fixture
def user(org):
    return User.objects.create_user(email="u@acme.com", password="pass123", organization=org)


@pytest.mark.django_db
class TestCachedProjectListView:
    def test_returns_projects_for_organization(self, user, org):
        Project.objects.create(organization=org, name="P1", created_by=user)

        request = factory.get("/api/projects/cached/")
        force_authenticate(request, user=user)
        response = CachedProjectListView.as_view()(request)

        assert response.status_code == 200
        assert len(response.data) == 1

    def test_second_request_uses_cache(self, user, org):
        Project.objects.create(organization=org, name="P1", created_by=user)

        request1 = factory.get("/api/projects/cached/")
        force_authenticate(request1, user=user)
        CachedProjectListView.as_view()(request1)

        # Create a second project directly in the DB without invalidating
        Project.objects.create(organization=org, name="P2", created_by=user)

        request2 = factory.get("/api/projects/cached/")
        force_authenticate(request2, user=user)
        response2 = CachedProjectListView.as_view()(request2)

        # Still shows only 1, proving the cached (stale) response was served
        assert len(response2.data) == 1

    def test_filters_by_status(self, user, org):
        Project.objects.create(organization=org, name="Active1", status="active", created_by=user)
        Project.objects.create(organization=org, name="Archived1", status="archived", created_by=user)

        request = factory.get("/api/projects/cached/", {"status": "archived"})
        force_authenticate(request, user=user)
        response = CachedProjectListView.as_view()(request)

        assert len(response.data) == 1
        assert response.data[0]["name"] == "Archived1"


@pytest.mark.django_db
class TestCachedProjectCreateView:
    def test_creates_project(self, user, org):
        request = factory.post(
            "/api/projects/cached/create/", {"name": "New Project"}, format="json"
        )
        force_authenticate(request, user=user)
        response = CachedProjectCreateView.as_view()(request)

        assert response.status_code == 201
        assert Project.objects.filter(organization=org, name="New Project").exists()

    def test_cache_invalidation_correctly_clears_stale_list_cache(self, user, org):
        """
        Confirms cache_service.invalidate_pattern() correctly clears the
        list cache after a new project is created — invalidation works
        as intended despite the two views using different caching
        mechanisms (Django's cache.set() for reads, raw redis_client
        pattern matching for invalidation).
        """
        list_request = factory.get("/api/projects/cached/")
        force_authenticate(list_request, user=user)
        CachedProjectListView.as_view()(list_request)  # caches an empty list

        create_request = factory.post(
            "/api/projects/cached/create/", {"name": "New Project"}, format="json"
        )
        force_authenticate(create_request, user=user)
        CachedProjectCreateView.as_view()(create_request)

        list_request2 = factory.get("/api/projects/cached/")
        force_authenticate(list_request2, user=user)
        response2 = CachedProjectListView.as_view()(list_request2)

        assert len(response2.data) == 1
        assert response2.data[0]["name"] == "New Project"