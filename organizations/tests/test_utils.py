import pytest
from unittest.mock import Mock

from organizations.utils import check_plan_limit_middleware


class TestCheckPlanLimitMiddleware:
    """
    Note: this middleware is not registered in MIDDLEWARE and its
    body is currently a no-op (the free-plan branch just does `pass`,
    with no actual restriction logic). These tests confirm its
    current pass-through behavior, not any real enforcement.
    """

    def test_passes_through_for_unauthenticated_user(self):
        get_response = Mock(return_value="response")
        middleware = check_plan_limit_middleware(get_response)

        request = Mock()
        request.user.is_authenticated = False

        result = middleware(request)

        assert result == "response"
        get_response.assert_called_once_with(request)

    def test_passes_through_for_free_plan_org_with_no_restriction_applied(self):
        get_response = Mock(return_value="response")
        middleware = check_plan_limit_middleware(get_response)

        request = Mock()
        request.user.is_authenticated = True
        request.user.organization = Mock(plan="free")

        result = middleware(request)

        assert result == "response"

    def test_passes_through_for_paid_plan_org(self):
        get_response = Mock(return_value="response")
        middleware = check_plan_limit_middleware(get_response)

        request = Mock()
        request.user.is_authenticated = True
        request.user.organization = Mock(plan="pro")

        result = middleware(request)

        assert result == "response"