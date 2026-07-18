import pytest
from unittest.mock import MagicMock, patch
from django.test import RequestFactory, override_settings

from core.middleware_rate_limit import GlobalRateLimitMiddleware

factory = RequestFactory()


def make_middleware():
    get_response = MagicMock(return_value="ok_response")
    return GlobalRateLimitMiddleware(get_response), get_response


class TestGlobalRateLimitMiddleware:

    def test_passes_through_when_testing_flag_is_true(self):
        middleware, get_response = make_middleware()
        request = factory.get("/api/projects/")

        with override_settings(TESTING=True):
            response = middleware(request)

        assert response == "ok_response"
        get_response.assert_called_once()

    @override_settings(TESTING=False)
    def test_admin_path_bypasses_rate_limiting(self):
        middleware, get_response = make_middleware()
        request = factory.get("/admin/login/")

        response = middleware(request)

        assert response == "ok_response"

    @override_settings(TESTING=False)
    def test_static_path_bypasses_rate_limiting(self):
        middleware, get_response = make_middleware()
        request = factory.get("/static/style.css")

        response = middleware(request)

        assert response == "ok_response"

    @override_settings(TESTING=False)
    @patch("core.middleware_rate_limit.cache")
    def test_under_limit_allows_request_and_increments_counter(self, mock_cache):
        mock_cache.get.return_value = 5
        middleware, get_response = make_middleware()
        request = factory.get("/api/projects/")

        response = middleware(request)

        assert response == "ok_response"
        mock_cache.set.assert_called_once()
        args, kwargs = mock_cache.set.call_args
        assert args[1] == 6  # incremented

    @override_settings(TESTING=False)
    @patch("core.middleware_rate_limit.cache")
    def test_at_default_limit_returns_429(self, mock_cache):
        mock_cache.get.return_value = 100  # DEFAULT limit
        middleware, get_response = make_middleware()
        request = factory.get("/api/projects/")

        response = middleware(request)

        assert response.status_code == 429
        get_response.assert_not_called()

    @override_settings(TESTING=False)
    @patch("core.middleware_rate_limit.cache")
    def test_auth_path_uses_stricter_limit(self, mock_cache):
        mock_cache.get.return_value = 30  # auth limit is 30, so this is AT limit
        middleware, get_response = make_middleware()
        request = factory.get("/api/auth/login/")

        response = middleware(request)

        assert response.status_code == 429
        import json
        data = json.loads(response.content)
        assert data["limit"] == 30

    @override_settings(TESTING=False)
    @patch("core.middleware_rate_limit.cache")
    def test_search_path_uses_stricter_limit(self, mock_cache):
        mock_cache.get.return_value = 19  # search limit is 20, still under
        middleware, get_response = make_middleware()
        request = factory.get("/api/search/?q=test")

        response = middleware(request)

        assert response == "ok_response"
        args, kwargs = mock_cache.set.call_args
        assert args[1] == 20

    @override_settings(TESTING=False)
    @patch("core.middleware_rate_limit.cache")
    def test_uses_x_forwarded_for_when_present(self, mock_cache):
        mock_cache.get.return_value = 0
        middleware, get_response = make_middleware()
        request = factory.get(
            "/api/projects/", HTTP_X_FORWARDED_FOR="203.0.113.5, 10.0.0.1"
        )

        middleware(request)

        cache_key_used = mock_cache.get.call_args[0][0]
        assert "203.0.113.5" in cache_key_used

    @override_settings(TESTING=False)
    @patch("core.middleware_rate_limit.cache")
    def test_falls_back_to_remote_addr_without_forwarded_header(self, mock_cache):
        mock_cache.get.return_value = 0
        middleware, get_response = make_middleware()
        request = factory.get("/api/projects/", REMOTE_ADDR="192.168.1.1")

        middleware(request)

        cache_key_used = mock_cache.get.call_args[0][0]
        assert "192.168.1.1" in cache_key_used