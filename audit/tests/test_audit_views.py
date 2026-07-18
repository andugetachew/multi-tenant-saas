import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from organizations.models import Organization
from accounts.models import User
from audit.models import AuditLog
from audit.views import AuditLogListView, AuditLogDetailView

factory = APIRequestFactory()


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
class TestAuditLogListView:
    def test_owner_sees_all_org_logs(self, owner, member, org):
            AuditLog.objects.create(
                organization=org, user=member, action="CREATE", model_name="Project",
                object_id=1, object_name="P1", ip_address="1.1.1.1",
            )
            AuditLog.objects.create(
                organization=org, user=owner, action="UPDATE", model_name="Task",
                object_id=2, object_name="T1", ip_address="1.1.1.1",
            )

            request = factory.get("/api/audit/")
            force_authenticate(request, user=owner)
            response = AuditLogListView.as_view()(request)

            assert response.status_code == 200
            assert len(response.data["results"]) == 2

    def test_member_only_sees_own_logs(self, member, owner, org):
        AuditLog.objects.create(
            organization=org, user=member, action="CREATE", model_name="Project",
            object_id=1, object_name="Mine", ip_address="1.1.1.1",
        )
        AuditLog.objects.create(
            organization=org, user=owner, action="CREATE", model_name="Project",
            object_id=2, object_name="NotMine", ip_address="1.1.1.1",
        )

        request = factory.get("/api/audit/")
        force_authenticate(request, user=member)
        response = AuditLogListView.as_view()(request)

        results = response.data["results"]
        assert len(results) == 1
        assert results[0]["object_name"] == "Mine"

     


@pytest.mark.django_db
class TestAuditLogDetailView:
    def test_retrieves_log_in_own_organization(self, owner, org):
        log = AuditLog.objects.create(
            organization=org, user=owner, action="DELETE", model_name="Task",
            object_id=5, object_name="T5", ip_address="1.1.1.1",
        )

        request = factory.get(f"/api/audit/{log.id}/")
        force_authenticate(request, user=owner)
        response = AuditLogDetailView.as_view()(request, pk=log.id)

        assert response.status_code == 200
        assert response.data["object_name"] == "T5"