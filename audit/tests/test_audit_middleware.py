import pytest
from unittest.mock import Mock
from django.http import JsonResponse

from organizations.models import Organization
from accounts.models import User
from audit.models import AuditLog
from audit.middleware import AuditMiddleware


@pytest.fixture
def org(db):
    return Organization.objects.create(name="Acme Corp")


@pytest.fixture
def user(org):
    return User.objects.create_user(email="u@acme.com", password="pass123", organization=org)


def make_middleware():
    get_response = Mock(return_value=JsonResponse({"ok": True}))
    return AuditMiddleware(get_response), get_response


@pytest.mark.django_db
class TestAuditMiddleware:

    def test_unauthenticated_request_is_not_logged(self, rf):
        middleware, get_response = make_middleware()
        request = rf.post("/api/projects/")
        request.user = Mock(is_authenticated=False)

        middleware(request)

        get_response.assert_called_once()
        assert AuditLog.objects.count() == 0

    def test_get_request_is_not_logged(self, rf, user):
        middleware, get_response = make_middleware()
        request = rf.get("/api/projects/")
        request.user = user

        middleware(request)

        assert AuditLog.objects.count() == 0

    def test_post_request_logs_create_action(self, rf, user, org):
        middleware, get_response = make_middleware()
        request = rf.post("/api/projects/")
        request.user = user

        middleware(request)

        log = AuditLog.objects.get()
        assert log.action == "CREATE"
        assert log.organization == org
        assert log.user == user
        assert log.object_name == "/api/projects/"
        assert log.new_values == {"method": "POST", "path": "/api/projects/"}

    def test_put_request_logs_update_action(self, rf, user):
        middleware, get_response = make_middleware()
        request = rf.put("/api/projects/1/")
        request.user = user

        middleware(request)

        log = AuditLog.objects.get()
        assert log.action == "UPDATE"

    def test_patch_request_logs_update_action(self, rf, user):
        middleware, get_response = make_middleware()
        request = rf.patch("/api/projects/1/")
        request.user = user

        middleware(request)

        log = AuditLog.objects.get()
        assert log.action == "UPDATE"

    def test_delete_request_logs_delete_action(self, rf, user):
        middleware, get_response = make_middleware()
        request = rf.delete("/api/projects/1/")
        request.user = user

        middleware(request)

        log = AuditLog.objects.get()
        assert log.action == "DELETE"

    def test_authenticated_user_without_organization_does_not_crash(self, rf, org):
        middleware, get_response = make_middleware()
        request = rf.post("/api/projects/")
        request.user = Mock(is_authenticated=True, organization=None)

        response = middleware(request)

        assert response.status_code == 200
        assert AuditLog.objects.count() == 0

    def test_ip_and_user_agent_are_captured(self, rf, user):
        middleware, get_response = make_middleware()
        request = rf.post(
            "/api/projects/",
            REMOTE_ADDR="203.0.113.5",
            HTTP_USER_AGENT="pytest-test-agent",
        )
        request.user = user

        middleware(request)

        log = AuditLog.objects.get()
        assert log.ip_address == "203.0.113.5"
        assert log.user_agent == "pytest-test-agent"