import pytest
from unittest.mock import Mock
from django.http import JsonResponse

from organizations.models import Organization
from accounts.models import User
from billing.models import Plan, Subscription
from billing.middleware import PlanLimitMiddleware


@pytest.fixture
def org(db):
    return Organization.objects.create(name="Acme Corp")


@pytest.fixture
def user(org):
    return User.objects.create_user(email="u@acme.com", password="pass123", organization=org)


@pytest.fixture
def active_subscription_with_limits(org):
    plan = Plan.objects.create(
        name="Basic", slug="basic", max_projects=2, max_users=3,
        has_real_time_analytics=False, has_advanced_exports=False,
    )
    return Subscription.objects.create(
        organization=org, plan=plan, status="active",
        max_projects=2, max_users=3,
        has_real_time_analytics=False, has_advanced_exports=False,
    )


def make_middleware(response_body=b"OK"):
    get_response = Mock(return_value=JsonResponse({"ok": True}))
    return PlanLimitMiddleware(get_response), get_response


@pytest.mark.django_db
class TestPlanLimitMiddleware:

    def test_unauthenticated_request_passes_through(self, rf):
        middleware, get_response = make_middleware()
        request = rf.post("/api/projects/")
        request.user = Mock(is_authenticated=False)

        response = middleware(request)

        get_response.assert_called_once_with(request)
        assert response.status_code == 200

    def test_project_creation_blocked_when_limit_reached(
        self, rf, user, org, active_subscription_with_limits
    ):
        from projects.models import Project
        Project.objects.create(organization=org, name="P1", created_by=user)
        Project.objects.create(organization=org, name="P2", created_by=user)  # at limit of 2

        middleware, get_response = make_middleware()
        request = rf.post("/api/projects/")
        request.user = user

        response = middleware(request)

        assert response.status_code == 403
        get_response.assert_not_called()

    def test_project_creation_allowed_under_limit(
        self, rf, user, org, active_subscription_with_limits
    ):
        middleware, get_response = make_middleware()
        request = rf.post("/api/projects/")
        request.user = user

        response = middleware(request)

        get_response.assert_called_once()
        assert response.status_code == 200
    def test_realtime_analytics_blocked_without_feature(
        self, rf, user, org, active_subscription_with_limits
    ):
        middleware, get_response = make_middleware()
        request = rf.get("/api/dashboard/realtime/")
        request.user = user

        response = middleware(request)

        assert response.status_code == 403
        get_response.assert_not_called()

    def test_realtime_analytics_allowed_with_feature(self, rf, user, org):
        plan = Plan.objects.create(
            name="Pro Test Plan", slug="pro-test-plan-realtime", has_real_time_analytics=True,
        )
        Subscription.objects.create(
            organization=org, plan=plan, status="active",
            has_real_time_analytics=True,
        )

        middleware, get_response = make_middleware()
        request = rf.get("/api/dashboard/realtime/")
        request.user = user

        response = middleware(request)

        get_response.assert_called_once()
        assert response.status_code == 200

    def test_get_requests_to_projects_endpoint_are_not_limited(
        self, rf, user, org, active_subscription_with_limits
    ):
        """Only POST triggers the project-limit check, per the middleware's own logic."""
        middleware, get_response = make_middleware()
        request = rf.get("/api/projects/")
        request.user = user

        response = middleware(request)

        get_response.assert_called_once()
        assert response.status_code == 200