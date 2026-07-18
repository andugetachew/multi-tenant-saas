import pytest
from unittest.mock import Mock, patch
from rest_framework.exceptions import Throttled

from core.rate_limits import (
    TieredRateLimiter,
    RateLimitThrottle,
    AuthLoginThrottle,
    AuthRegisterThrottle,
    SearchGlobalThrottle,
    ProjectCreateThrottle,
)


def make_request(authenticated=True, user_id=1, org_id=5, ip="203.0.113.5", forwarded=None):
    request = Mock()
    request.user = Mock(is_authenticated=authenticated, id=user_id, organization_id=org_id)
    request.META = {"REMOTE_ADDR": ip}
    if forwarded:
        request.META["HTTP_X_FORWARDED_FOR"] = forwarded
    return request


class TestGetClientIp:
    def test_uses_remote_addr_when_no_forwarded_header(self):
        limiter = TieredRateLimiter()
        request = make_request(ip="203.0.113.5")
        assert limiter.get_client_ip(request) == "203.0.113.5"

    def test_uses_first_ip_from_forwarded_header(self):
        limiter = TieredRateLimiter()
        request = make_request(forwarded="203.0.113.5, 10.0.0.1")
        assert limiter.get_client_ip(request) == "203.0.113.5"


class TestGetKey:
    def test_ip_strategy(self):
        limiter = TieredRateLimiter()
        request = make_request(ip="1.2.3.4")
        key = limiter.get_key(request, "auth_register", "ip")
        assert key == "ratelimit:auth_register:ip:1.2.3.4"

    def test_user_strategy_authenticated(self):
        limiter = TieredRateLimiter()
        request = make_request(authenticated=True, user_id=42)
        key = limiter.get_key(request, "dashboard_stats", "user")
        assert key == "ratelimit:dashboard_stats:user:42"

    def test_user_strategy_unauthenticated(self):
        limiter = TieredRateLimiter()
        request = make_request(authenticated=False, ip="9.9.9.9")
        key = limiter.get_key(request, "dashboard_stats", "user")
        assert key == "ratelimit:dashboard_stats:anon:9.9.9.9"

    def test_ip_user_strategy_authenticated(self):
        limiter = TieredRateLimiter()
        request = make_request(authenticated=True, user_id=7, ip="1.1.1.1")
        key = limiter.get_key(request, "auth_login", "ip_user")
        assert key == "ratelimit:auth_login:1.1.1.1:user:7"

    def test_ip_user_strategy_unauthenticated(self):
        limiter = TieredRateLimiter()
        request = make_request(authenticated=False, ip="1.1.1.1")
        key = limiter.get_key(request, "auth_login", "ip_user")
        assert key == "ratelimit:auth_login:1.1.1.1"

    def test_user_org_strategy(self):
        limiter = TieredRateLimiter()
        request = make_request(authenticated=True, user_id=3, org_id=99)
        key = limiter.get_key(request, "project_create", "user_org")
        assert key == "ratelimit:project_create:org:99:user:3"

    def test_org_strategy(self):
        limiter = TieredRateLimiter()
        request = make_request(authenticated=True, org_id=99)
        key = limiter.get_key(request, "org_invite", "org")
        assert key == "ratelimit:org_invite:org:99"

    def test_org_strategy_unauthenticated_falls_back_to_anon(self):
        limiter = TieredRateLimiter()
        request = make_request(authenticated=False, ip="5.5.5.5")
        key = limiter.get_key(request, "org_invite", "org")
        assert key == "ratelimit:org_invite:anon:5.5.5.5"

    def test_unknown_strategy_falls_back_to_ip_only(self):
        limiter = TieredRateLimiter()
        request = make_request(ip="8.8.8.8")
        key = limiter.get_key(request, "some_endpoint", "unknown_strategy")
        assert key == "ratelimit:some_endpoint:8.8.8.8"


class TestCheckRateLimit:
    @patch("core.rate_limits.cache")
    def test_unknown_endpoint_always_allowed(self, mock_cache):
        limiter = TieredRateLimiter()
        request = make_request()
        allowed, block = limiter.check_rate_limit(request, "not_a_real_endpoint")
        assert allowed is True
        assert block is None
        mock_cache.get.assert_not_called()

    @patch("core.rate_limits.cache")
    def test_under_limit_allows_and_increments(self, mock_cache):
        mock_cache.get.side_effect = lambda key, default=None: (
            False if key.endswith(":blocked") else 2
        )
        limiter = TieredRateLimiter()
        request = make_request(authenticated=True, user_id=1)

        allowed, block = limiter.check_rate_limit(request, "auth_login")

        assert allowed is True
        assert block is None
        mock_cache.set.assert_called_once()
        args, kwargs = mock_cache.set.call_args
        assert args[1] == 3  # incremented from 2 to 3

    @patch("core.rate_limits.cache")
    def test_at_limit_blocks_and_sets_block_key(self, mock_cache):
        mock_cache.get.side_effect = lambda key, default=None: (
            False if key.endswith(":blocked") else 5
        )
        limiter = TieredRateLimiter()
        request = make_request(authenticated=True, user_id=1)

        allowed, block = limiter.check_rate_limit(request, "auth_login")

        assert allowed is False
        assert block == 900
        block_call = [c for c in mock_cache.set.call_args_list if c.args[0].endswith(":blocked")]
        assert len(block_call) == 1

    @patch("core.rate_limits.cache")
    def test_already_blocked_denies_immediately(self, mock_cache):
        mock_cache.get.side_effect = lambda key, default=None: (
            True if key.endswith(":blocked") else default
        )
        limiter = TieredRateLimiter()
        request = make_request(authenticated=True, user_id=1)

        allowed, block = limiter.check_rate_limit(request, "auth_register")

        assert allowed is False
        assert block == 3600


class TestRateLimitThrottle:
    def test_no_endpoint_key_always_allows(self):
        throttle = RateLimitThrottle()
        request = make_request()
        assert throttle.allow_request(request, None) is True

    @patch("core.rate_limits.rate_limiter")
    def test_allowed_request_returns_true(self, mock_limiter):
        mock_limiter.check_rate_limit.return_value = (True, None)
        throttle = RateLimitThrottle()
        throttle.set_endpoint_key("auth_login")
        request = make_request()
        assert throttle.allow_request(request, None) is True

    @patch("core.rate_limits.rate_limiter")
    def test_disallowed_request_raises_throttled(self, mock_limiter):
        mock_limiter.check_rate_limit.return_value = (False, 900)
        throttle = RateLimitThrottle()
        throttle.set_endpoint_key("auth_login")
        request = make_request()
        with pytest.raises(Throttled):
            throttle.allow_request(request, None)


class TestIndividualThrottleClasses:
    def test_auth_login_throttle_sets_correct_key(self):
        assert AuthLoginThrottle().endpoint_key == "auth_login"

    def test_auth_register_throttle_sets_correct_key(self):
        assert AuthRegisterThrottle().endpoint_key == "auth_register"

    def test_search_global_throttle_sets_correct_key(self):
        assert SearchGlobalThrottle().endpoint_key == "search_global"

    def test_project_create_throttle_sets_correct_key(self):
        assert ProjectCreateThrottle().endpoint_key == "project_create"