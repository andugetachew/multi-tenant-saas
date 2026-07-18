import json
import pytest
from unittest.mock import MagicMock
from rest_framework.test import APIRequestFactory, force_authenticate

from organizations.models import Organization
from accounts.models import User
from projects.models import Project, Task
from search.cached_views import CachedGlobalSearchView
from core.cache_config import cache_service

factory = APIRequestFactory()


@pytest.fixture
def org(db):
    return Organization.objects.create(name="Acme Corp")


@pytest.fixture
def user(org):
    return User.objects.create_user(email="u@acme.com", password="pass123", organization=org)


@pytest.fixture
def mock_redis(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr(cache_service, "redis_client", mock)
    return mock


def make_request(user, query=None):
    params = {"q": query} if query is not None else {}
    request = factory.get("/api/search/", params)
    force_authenticate(request, user=user)
    return request


class TestNormalizeQuery:
    def test_lowercases_and_strips_stopwords(self):
        view = CachedGlobalSearchView()
        result = view.normalize_query("The Quick Brown Fox")
        assert result == "brown fox quick"  # stopword "the" removed, sorted

    def test_sorts_words_for_consistent_key(self):
        view = CachedGlobalSearchView()
        assert view.normalize_query("zebra apple") == view.normalize_query("apple zebra")


class TestGetCacheTtl:
    def test_long_query_gets_short_ttl(self):
        view = CachedGlobalSearchView()
        assert view.get_cache_ttl("one two three four five six") == 30

    def test_short_query_gets_medium_ttl(self):
        view = CachedGlobalSearchView()
        assert view.get_cache_ttl("cat") == 120

    def test_default_ttl_for_moderate_query(self):
        view = CachedGlobalSearchView()
        assert view.get_cache_ttl("notifications") == 60


@pytest.mark.django_db
class TestCachedGlobalSearchView:

    def test_empty_query_returns_400(self, user):
        request = make_request(user, query="")
        view = CachedGlobalSearchView.as_view()
        response = view(request)
        assert response.status_code == 400

    def test_cache_hit_returns_cached_results_without_search(self, mock_redis, user):
        cached_payload = {"projects": [], "tasks": [], "comments": []}
        mock_redis.get.return_value = json.dumps(cached_payload)

        request = make_request(user, query="dashboard")
        view = CachedGlobalSearchView.as_view()
        response = view(request)

        assert response.status_code == 200
        assert response.data == cached_payload

    def test_cache_miss_computes_and_caches_results(self, mock_redis, user, org):
        mock_redis.get.return_value = None
        Project.objects.create(organization=org, name="dashboard project")

        request = make_request(user, query="dashboard")
        view = CachedGlobalSearchView.as_view()
        response = view(request)

        assert response.status_code == 200
        assert len(response.data["projects"]) == 1
        mock_redis.setex.assert_called_once()