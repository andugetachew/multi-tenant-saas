import json
import pytest
from unittest.mock import MagicMock, patch
from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from organizations.models import Organization
from accounts.models import User
from dashboard.cached_views import CachedRealTimeDashboardView, CachedDashboardStatsView
from core.cache_config import cache_service

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


factory = APIRequestFactory()


def make_authed_request(user, path="/api/dashboard/"):
    request = factory.get(path)
    force_authenticate(request, user=user)
    return request


@pytest.mark.django_db
class TestCachedRealTimeDashboardView:

    def test_layer1_user_cache_hit_returns_cached_data_without_computation(
        self, mock_redis, user
    ):
        cached_payload = {"total_projects": 5, "_cached_at": "2026-01-01T00:00:00"}
        mock_redis.get.side_effect = [json.dumps(cached_payload)]  # first call: user cache hit

        view = CachedRealTimeDashboardView.as_view()
        request = make_authed_request(user)
        response = view(request)

        assert response.status_code == 200
        assert response.data == cached_payload
        # Only one redis GET should happen — user-cache hit short-circuits everything else
        assert mock_redis.get.call_count == 1
        mock_redis.setex.assert_not_called()

    def test_layer2_org_cache_hit_warms_user_cache_and_returns_data(self, mock_redis, user):
        org_payload = {"total_projects": 3, "_cached_at": "2026-01-01T00:00:00"}
        # First get() call (user cache) -> None, second get() call (org cache) -> hit
        mock_redis.get.side_effect = [None, json.dumps(org_payload)]

        view = CachedRealTimeDashboardView.as_view()
        request = make_authed_request(user)
        response = view(request)

        assert response.status_code == 200
        assert response.data == org_payload
        # Should warm the user-specific cache for 5 seconds
        mock_redis.setex.assert_called_once()
        args, kwargs = mock_redis.setex.call_args
        assert args[1] == 5  # ttl seconds
        assert json.loads(args[2]) == org_payload

    def test_layer3_full_cache_miss_computes_fresh_and_warms_both_caches(
        self, mock_redis, user, org
    ):
        mock_redis.get.side_effect = [None, None]  # both user and org cache miss

        view = CachedRealTimeDashboardView.as_view()
        request = make_authed_request(user)
        response = view(request)

        assert response.status_code == 200
        assert response.data["total_projects"] == 0
        assert response.data["total_tasks"] == 0
        assert "_cached_at" in response.data
        # Should warm both org (30s) and user (5s) caches
        assert mock_redis.setex.call_count == 2
        ttls_used = {call.args[1] for call in mock_redis.setex.call_args_list}
        assert ttls_used == {30, 5}


@pytest.mark.django_db
class TestCachedDashboardStatsView:

    def test_returns_cached_stats_without_recomputing(self, mock_redis, user):
        cached_stats = {"total_projects": 7, "_computed_at": "2026-01-01T00:00:00"}
        mock_redis.get.side_effect = [None, json.dumps(cached_stats)]

        view = CachedDashboardStatsView.as_view()
        request = make_authed_request(user)
        response = view(request)

        assert response.status_code == 200
        assert response.data == cached_stats
        mock_redis.setex.assert_not_called()

    def test_computes_and_caches_stats_when_cache_empty(self, mock_redis, user, org):
        mock_redis.get.side_effect = [None, None]

        view = CachedDashboardStatsView.as_view()
        request = make_authed_request(user)
        response = view(request)

        assert response.status_code == 200
        assert response.data["organization_name"] == org.name
        mock_redis.setex.assert_called_once()

    def test_fresh_metadata_does_not_trigger_background_refresh(self, mock_redis, user):
        fresh_metadata = {"refreshed_at": timezone.now().timestamp() - 10}
        cached_stats = {"total_projects": 1}
        mock_redis.get.side_effect = [json.dumps(fresh_metadata), json.dumps(cached_stats)]

        view = CachedDashboardStatsView.as_view()
        request = make_authed_request(user)
        response = view(request)

        assert response.status_code == 200
        assert response.data == cached_stats

    @patch("dashboard.cached_views.CachedDashboardStatsView.trigger_background_refresh.delay")
    def test_stale_metadata_triggers_background_refresh(self, mock_delay, mock_redis, user):
        stale_metadata = {"refreshed_at": timezone.now().timestamp() - 400}
        cached_stats = {"total_projects": 2}
        mock_redis.get.side_effect = [json.dumps(stale_metadata), json.dumps(cached_stats)]

        view = CachedDashboardStatsView.as_view()
        request = make_authed_request(user)
        response = view(request)

        assert response.status_code == 200
        mock_delay.assert_called_once_with(user.organization_id)