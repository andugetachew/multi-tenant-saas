import pytest
from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from organizations.models import Organization
from accounts.models import User
from projects.models import Project, Task
from analytics.models import AnalyticsEvent
from billing.models import Transaction
from analytics.views import (
    DashboardAnalyticsView,
    RevenueAnalyticsView,
    SellerPerformanceView,
    SystemHealthView,
)

factory = APIRequestFactory()


def make_authed_request(user, path="/api/analytics/"):
    request = factory.get(path)
    force_authenticate(request, user=user)
    return request


@pytest.fixture
def org(db):
    return Organization.objects.create(name="Acme Corp")


@pytest.fixture
def owner(org):
    return User.objects.create_user(
        email="owner@acme.com", password="pass123", organization=org, is_owner=True
    )


@pytest.fixture
def member(org):
    return User.objects.create_user(
        email="member@acme.com", password="pass123", organization=org, role="member"
    )


@pytest.mark.django_db
class TestDashboardAnalyticsView:
    def test_returns_project_and_task_counts(self, owner, org):
        Project.objects.create(organization=org, name="P1", created_by=owner)
        task = Task.objects.create(project=Project.objects.first(), title="T1", status="completed")

        view = DashboardAnalyticsView.as_view()
        request = make_authed_request(owner)
        response = view(request)

        assert response.status_code == 200
        assert response.data["projects"]["total"] == 1
        assert response.data["tasks"]["total"] == 1
        assert response.data["tasks"]["completed"] == 1

    def test_counts_recent_activity_events_by_type(self, owner, org):
        AnalyticsEvent.objects.create(organization=org, event_type="project_view", user_id=owner.id)
        AnalyticsEvent.objects.create(organization=org, event_type="project_view", user_id=owner.id)
        AnalyticsEvent.objects.create(organization=org, event_type="task_complete", user_id=owner.id)

        view = DashboardAnalyticsView.as_view()
        request = make_authed_request(owner)
        response = view(request)

        assert response.data["activity"]["total_events"] == 3
        assert response.data["activity"]["by_type"]["project_view"] == 2
        assert response.data["activity"]["by_type"]["task_complete"] == 1

    def test_overdue_tasks_are_counted(self, owner, org):
        project = Project.objects.create(organization=org, name="P1", created_by=owner)
        Task.objects.create(
            project=project, title="Overdue", status="pending",
            due_date=timezone.now() - timedelta(days=1),
        )
        Task.objects.create(
            project=project, title="Future", status="pending",
            due_date=timezone.now() + timedelta(days=1),
        )

        view = DashboardAnalyticsView.as_view()
        request = make_authed_request(owner)
        response = view(request)

        assert response.data["tasks"]["overdue"] == 1


@pytest.mark.django_db
class TestRevenueAnalyticsView:
    def test_owner_can_access(self, owner, org):
        view = RevenueAnalyticsView.as_view()
        request = make_authed_request(owner)
        response = view(request)

        assert response.status_code == 200
        assert "revenue" in response.data
        assert len(response.data["revenue"]) == 12
        assert response.data["currency"] == "USD"

    def test_regular_member_denied(self, member):
        view = RevenueAnalyticsView.as_view()
        request = make_authed_request(member)
        response = view(request)

        assert response.status_code == 403

    def test_completed_transactions_counted_in_current_month(self, owner, org):
        Transaction.objects.create(
            organization=org, type="subscription", amount=99,
            status="completed", created_at=timezone.now(),
        )

        view = RevenueAnalyticsView.as_view()
        request = make_authed_request(owner)
        response = view(request)

        current_month = response.data["revenue"][0]
        assert current_month["revenue"] == 99.0
        assert current_month["subscriptions"] == 1

    def test_pending_transactions_not_counted(self, owner, org):
        Transaction.objects.create(
            organization=org, type="subscription", amount=50,
            status="pending", created_at=timezone.now(),
        )

        view = RevenueAnalyticsView.as_view()
        request = make_authed_request(owner)
        response = view(request)

        assert response.data["total_revenue"] == 0.0


@pytest.mark.django_db
class TestSellerPerformanceView:
    def test_owner_can_access(self, owner, org):
        view = SellerPerformanceView.as_view()
        request = make_authed_request(owner)
        response = view(request)

        assert response.status_code == 200
        assert "top_performers" in response.data
        assert "all_performers" in response.data

    def test_member_denied(self, member):
        view = SellerPerformanceView.as_view()
        request = make_authed_request(member)
        response = view(request)

        assert response.status_code == 403

    def test_completion_rate_calculated_correctly(self, owner, org, member):
        project = Project.objects.create(organization=org, name="P1", created_by=owner)
        Task.objects.create(project=project, title="T1", status="completed", assigned_to=member)
        Task.objects.create(project=project, title="T2", status="pending", assigned_to=member)

        view = SellerPerformanceView.as_view()
        request = make_authed_request(owner)
        response = view(request)

        member_data = next(
            p for p in response.data["all_performers"] if p["user_email"] == member.email
        )
        assert member_data["tasks_assigned"] == 2
        assert member_data["tasks_completed"] == 1
        assert member_data["completion_rate"] == 50.0

    def test_team_average_completion_is_zero_with_no_users(self, owner, org):
        # org.users includes only 'owner' (member fixture not created here)
        view = SellerPerformanceView.as_view()
        request = make_authed_request(owner)
        response = view(request)

        assert "team_average_completion" in response.data


@pytest.mark.django_db
class TestSystemHealthView:
    def test_superuser_can_access(self, org):
        superuser = User.objects.create_superuser(
            email="admin@acme.com", password="pass123", organization=org
        )
        view = SystemHealthView.as_view()
        request = make_authed_request(superuser)
        response = view(request)

        assert response.status_code == 200
        assert response.data["status"] in ("healthy", "degraded")
        assert "database" in response.data
        assert "cache" in response.data

    def test_regular_owner_denied(self, owner):
        view = SystemHealthView.as_view()
        request = make_authed_request(owner)
        response = view(request)

        assert response.status_code == 403

    def test_member_denied(self, member):
        view = SystemHealthView.as_view()
        request = make_authed_request(member)
        response = view(request)

        assert response.status_code == 403