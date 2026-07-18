import pytest
from django.core.cache import cache

from organizations.models import Organization
from accounts.models import User
from projects.models import Project
from billing.models import Plan, Subscription
from billing.utils import (
    get_organization_subscription,
    check_org_limit,
    get_remaining_limit,
    sync_org_from_subscription,
    check_feature_access,
)


@pytest.fixture(autouse=True)
def clean_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def org(db):
    return Organization.objects.create(name="Acme Corp")


@pytest.mark.django_db
class TestGetOrganizationSubscription:
    def test_returns_none_for_no_organization(self):
        assert get_organization_subscription(None) is None

    def test_returns_none_when_no_subscription_exists(self, org):
        assert get_organization_subscription(org) is None

    def test_returns_and_caches_subscription(self, org):
        plan = Plan.objects.create(name="Pro", slug="pro-utils-test")
        sub = Subscription.objects.create(organization=org, plan=plan, status="active")

        result = get_organization_subscription(org)
        assert result.id == sub.id

        result2 = get_organization_subscription(org)
        assert result2.id == sub.id


@pytest.mark.django_db
class TestCheckOrgLimit:
    def test_no_organization_always_allowed(self):
        assert check_org_limit(None, "projects") is True

    def test_no_subscription_always_allowed(self, org):
        assert check_org_limit(org, "projects") is True

    def test_inactive_subscription_always_allowed(self, org):
        plan = Plan.objects.create(name="Pro", slug="pro-limit-inactive")
        Subscription.objects.create(organization=org, plan=plan, status="canceled", max_projects=1)
        assert check_org_limit(org, "projects") is True

    def test_unknown_resource_type_allowed(self, org):
        plan = Plan.objects.create(name="Pro", slug="pro-limit-unknown")
        Subscription.objects.create(organization=org, plan=plan, status="active")
        assert check_org_limit(org, "unknown_resource") is True

    def test_unlimited_when_max_is_negative_one(self, org, django_user_model):
        plan = Plan.objects.create(name="Enterprise", slug="ent-limit-unlimited")
        Subscription.objects.create(
            organization=org, plan=plan, status="active", max_projects=-1
        )
        assert check_org_limit(org, "projects") is True

    def test_denies_when_at_project_limit(self, org):
        plan = Plan.objects.create(name="Basic", slug="basic-limit-1")
        Subscription.objects.create(
            organization=org, plan=plan, status="active", max_projects=1
        )
        user = User.objects.create_user(email="u@acme.com", password="pass123", organization=org)
        Project.objects.create(organization=org, name="P1", created_by=user)

        assert check_org_limit(org, "projects") is False

    def test_allows_under_project_limit(self, org):
        plan = Plan.objects.create(name="Basic", slug="basic-limit-2")
        Subscription.objects.create(
            organization=org, plan=plan, status="active", max_projects=5
        )
        assert check_org_limit(org, "projects") is True

    def test_checks_user_limit(self, org):
        plan = Plan.objects.create(name="Basic", slug="basic-limit-users")
        Subscription.objects.create(
            organization=org, plan=plan, status="active", max_users=1
        )
        User.objects.create_user(email="u@acme.com", password="pass123", organization=org)

        assert check_org_limit(org, "users") is False


@pytest.mark.django_db
class TestGetRemainingLimit:
    def test_no_organization_returns_999(self):
        assert get_remaining_limit(None, "projects") == 999

    def test_no_subscription_returns_zero(self, org):
        assert get_remaining_limit(org, "projects") == 0

    def test_inactive_subscription_returns_zero(self, org):
        plan = Plan.objects.create(name="Pro", slug="pro-remaining-inactive")
        Subscription.objects.create(organization=org, plan=plan, status="canceled")
        assert get_remaining_limit(org, "projects") == 0

    def test_unknown_resource_type_returns_zero(self, org):
        plan = Plan.objects.create(name="Pro", slug="pro-remaining-unknown")
        Subscription.objects.create(organization=org, plan=plan, status="active")
        assert get_remaining_limit(org, "unknown_resource") == 0

    def test_unlimited_when_max_is_negative_one(self, org):
        plan = Plan.objects.create(name="Enterprise", slug="ent-remaining-unlimited")
        Subscription.objects.create(
            organization=org, plan=plan, status="active", max_projects=-1
        )
        assert get_remaining_limit(org, "projects") == 999999

    def test_calculates_remaining_projects(self, org):
        plan = Plan.objects.create(name="Basic", slug="basic-remaining-1")
        Subscription.objects.create(
            organization=org, plan=plan, status="active", max_projects=5
        )
        user = User.objects.create_user(email="u@acme.com", password="pass123", organization=org)
        Project.objects.create(organization=org, name="P1", created_by=user)

        assert get_remaining_limit(org, "projects") == 4

    def test_never_returns_negative(self, org):
        plan = Plan.objects.create(name="Basic", slug="basic-remaining-negative")
        Subscription.objects.create(
            organization=org, plan=plan, status="active", max_projects=1
        )
        user = User.objects.create_user(email="u@acme.com", password="pass123", organization=org)
        Project.objects.create(organization=org, name="P1", created_by=user)
        Project.objects.create(organization=org, name="P2", created_by=user)

        assert get_remaining_limit(org, "projects") == 0

    def test_calculates_remaining_users(self, org):
        plan = Plan.objects.create(name="Basic", slug="basic-remaining-users")
        Subscription.objects.create(
            organization=org, plan=plan, status="active", max_users=3
        )
        assert get_remaining_limit(org, "users") == 3


@pytest.mark.django_db
class TestSyncOrgFromSubscription:
    def test_syncs_plan_slug_and_status(self, org):
        plan = Plan.objects.create(name="Pro", slug="pro-sync-test")
        sub = Subscription.objects.create(organization=org, plan=plan, status="active")

        sync_org_from_subscription(sub)
        org.refresh_from_db()

        assert org.plan == "pro-sync-test"
        assert org.subscription_status == "active"

    def test_syncs_free_when_no_plan(self, org):
        sub = Subscription.objects.create(organization=org, plan=None, status="active")

        sync_org_from_subscription(sub)
        org.refresh_from_db()

        assert org.plan == "free"


@pytest.mark.django_db
class TestCheckFeatureAccess:
    def test_no_organization_denied(self):
        assert check_feature_access(None, "realtime_analytics") is False

    def test_no_subscription_denied(self, org):
        assert check_feature_access(org, "realtime_analytics") is False

    def test_inactive_subscription_denied(self, org):
        plan = Plan.objects.create(name="Pro", slug="pro-feature-inactive")
        Subscription.objects.create(
            organization=org, plan=plan, status="canceled", has_real_time_analytics=True
        )
        assert check_feature_access(org, "realtime_analytics") is False

    def test_unknown_feature_name_denied(self, org):
        plan = Plan.objects.create(name="Pro", slug="pro-feature-unknown")
        Subscription.objects.create(organization=org, plan=plan, status="active")
        assert check_feature_access(org, "not_a_real_feature") is False

    def test_grants_access_when_plan_has_feature(self, org):
        plan = Plan.objects.create(name="Pro", slug="pro-feature-granted")
        Subscription.objects.create(
            organization=org, plan=plan, status="active", has_advanced_exports=True
        )
        assert check_feature_access(org, "advanced_exports") is True

    def test_denies_when_plan_lacks_feature(self, org):
        plan = Plan.objects.create(name="Basic", slug="basic-feature-denied")
        Subscription.objects.create(
            organization=org, plan=plan, status="active", has_advanced_exports=False
        )
        assert check_feature_access(org, "advanced_exports") is False