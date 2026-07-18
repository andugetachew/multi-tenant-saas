import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from organizations.models import Organization
from accounts.models import User
from billing.models import Plan, Subscription, Invoice
from billing.views import PlanListView, CurrentSubscriptionView, RequestUpgradeView

factory = APIRequestFactory()


@pytest.fixture
def org(db):
    return Organization.objects.create(name="Acme Corp")


@pytest.fixture
def owner(org):
    return User.objects.create_user(
        email="owner@acme.com", password="pass123", organization=org, is_owner=True
    )


def make_authed_request(method, user, path="/api/billing/", data=None):
    if method == "get":
        request = factory.get(path)
    else:
        request = factory.post(path, data or {}, format="json")
    force_authenticate(request, user=user)
    return request


@pytest.mark.django_db
class TestPlanListView:
    def test_lists_only_active_plans(self, owner):
        Plan.objects.create(name="Basic", slug="basic-test", is_active=True)
        Plan.objects.create(name="Old", slug="old-test", is_active=False)

        request = make_authed_request("get", owner)
        view = PlanListView.as_view()
        response = view(request)

        assert response.status_code == 200
        slugs = [p["slug"] for p in response.data["results"]]
        assert "basic-test" in slugs
        assert "old-test" not in slugs


@pytest.mark.django_db
class TestCurrentSubscriptionView:
    def test_returns_free_defaults_when_no_subscription(self, owner):
        request = make_authed_request("get", owner)
        view = CurrentSubscriptionView.as_view()
        response = view(request)

        assert response.status_code == 200
        assert response.data["plan"] == "Free"
        assert response.data["features"]["max_projects"] == 3

    def test_returns_serialized_subscription_when_active(self, owner, org):
        plan = Plan.objects.create(name="Pro", slug="pro-test-current")
        Subscription.objects.create(organization=org, plan=plan, status="active")

        request = make_authed_request("get", owner)
        view = CurrentSubscriptionView.as_view()
        response = view(request)

        assert response.status_code == 200
        assert response.data["status"] == "active"


@pytest.mark.django_db
class TestRequestUpgradeView:
    def test_non_owner_denied(self, org):
        member = User.objects.create_user(
            email="member@acme.com", password="pass123", organization=org, is_owner=False
        )
        request = make_authed_request("post", member, data={"plan_slug": "pro"})
        view = RequestUpgradeView.as_view()
        response = view(request)

        assert response.status_code == 403

    def test_invalid_plan_slug_returns_400(self, owner):
        request = make_authed_request("post", owner, data={"plan_slug": "does-not-exist"})
        view = RequestUpgradeView.as_view()
        response = view(request)

        assert response.status_code == 400

    def test_creates_pending_invoice_for_valid_plan(self, owner, org):
        plan = Plan.objects.create(name="Pro", slug="pro-test-upgrade", price_monthly=49)

        request = make_authed_request("post", owner, data={"plan_slug": "pro-test-upgrade"})
        view = RequestUpgradeView.as_view()
        response = view(request)

        assert response.status_code == 202
        assert response.data["status"] == "pending"
        invoice = Invoice.objects.get(id=response.data["invoice_id"])
        assert invoice.requested_plan == plan
        assert invoice.organization == org

    def test_already_on_active_plan_returns_400(self, owner, org):
        plan = Plan.objects.create(name="Pro", slug="pro-test-already", price_monthly=49)
        Subscription.objects.create(organization=org, plan=plan, status="active")

        request = make_authed_request("post", owner, data={"plan_slug": "pro-test-already"})
        view = RequestUpgradeView.as_view()
        response = view(request)

        assert response.status_code == 400