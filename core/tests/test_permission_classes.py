import pytest
from unittest.mock import Mock, patch
from rest_framework.exceptions import PermissionDenied

from core.permissions import (
    IsOwnerOrReadOnly,
    IsOrganizationMember,
    IsAdminOrReadOnly,
    IsOwnerOrAdmin,
    IsViewerOrHigher,
    CanInviteUsers,
    CanManageBilling,
    CanExportData,
    IsSuperUser,
    ReadOnly,
    RateLimitExempt,
    OrganizationQuotaCheck,
    IsVerifiedUser,
    TwoFactorRequired,
)


def make_user(**kwargs):
    defaults = dict(
        is_authenticated=True, is_superuser=False, is_owner=False,
        role="member", organization_id=1, organization=Mock(id=1),
        email="u@test.com", is_email_verified=True, two_factor_enabled=False,
    )
    defaults.update(kwargs)
    return Mock(**defaults)


def make_request(method="GET", user=None, session=None, meta=None):
    request = Mock(method=method, user=user or make_user())
    request.session = session if session is not None else {}
    request.META = meta or {}
    return request


class TestIsOwnerOrReadOnly:
    def test_safe_method_always_allowed(self):
        perm = IsOwnerOrReadOnly()
        request = make_request(method="GET")
        obj = Mock(created_by=Mock())
        assert perm.has_object_permission(request, None, obj) is True

    def test_write_allowed_for_owner(self):
        perm = IsOwnerOrReadOnly()
        user = make_user()
        request = make_request(method="POST", user=user)
        obj = Mock(created_by=user)
        assert perm.has_object_permission(request, None, obj) is True

    def test_write_denied_for_non_owner(self):
        perm = IsOwnerOrReadOnly()
        request = make_request(method="POST", user=make_user())
        obj = Mock(created_by=Mock())
        assert perm.has_object_permission(request, None, obj) is False


class TestIsOrganizationMember:
    def test_unauthenticated_denied(self):
        perm = IsOrganizationMember()
        request = make_request(user=make_user(is_authenticated=False))
        assert perm.has_permission(request, None) is False

    def test_superuser_always_allowed(self):
        perm = IsOrganizationMember()
        request = make_request(user=make_user(is_superuser=True, organization_id=None))
        assert perm.has_permission(request, None) is True

    def test_no_organization_denied(self):
        perm = IsOrganizationMember()
        request = make_request(user=make_user(organization_id=None))
        assert perm.has_permission(request, None) is False

    def test_with_organization_allowed(self):
        perm = IsOrganizationMember()
        request = make_request(user=make_user(organization_id=5))
        assert perm.has_permission(request, None) is True

    def test_object_permission_matches_organization_directly(self):
        perm = IsOrganizationMember()
        user = make_user(organization_id=5)
        request = make_request(user=user)
        obj = Mock(spec=["organization", "organization_id"], organization_id=5)
        assert perm.has_object_permission(request, None, obj) is True

    def test_object_permission_denies_mismatched_organization(self):
        perm = IsOrganizationMember()
        user = make_user(organization_id=5)
        request = make_request(user=user)
        obj = Mock(spec=["organization_id"], organization_id=99)
        assert perm.has_object_permission(request, None, obj) is False

    def test_object_permission_falls_back_to_project_organization(self):
        perm = IsOrganizationMember()
        user = make_user(organization_id=5)
        request = make_request(user=user)
        obj = Mock(spec=["project"], project=Mock(organization_id=5))
        assert perm.has_object_permission(request, None, obj) is True

    def test_object_permission_falls_back_to_user_match(self):
        perm = IsOrganizationMember()
        user = make_user(organization_id=5)
        request = make_request(user=user)
        obj = Mock(spec=["user"], user=user)
        assert perm.has_object_permission(request, None, obj) is True

    def test_object_permission_denies_when_no_match(self):
        perm = IsOrganizationMember()
        request = make_request(user=make_user())
        obj = Mock(spec=[])
        assert perm.has_object_permission(request, None, obj) is False


class TestIsAdminOrReadOnly:
    def test_safe_method_allowed_without_auth(self):
        perm = IsAdminOrReadOnly()
        request = make_request(method="GET", user=make_user(is_authenticated=False))
        assert perm.has_permission(request, None) is True

    def test_write_denied_unauthenticated(self):
        perm = IsAdminOrReadOnly()
        request = make_request(method="POST", user=make_user(is_authenticated=False))
        assert perm.has_permission(request, None) is False

    def test_write_allowed_for_admin_role(self):
        perm = IsAdminOrReadOnly()
        request = make_request(method="POST", user=make_user(role="admin"))
        assert perm.has_permission(request, None) is True

    def test_write_allowed_for_owner(self):
        perm = IsAdminOrReadOnly()
        request = make_request(method="POST", user=make_user(is_owner=True))
        assert perm.has_permission(request, None) is True

    def test_write_denied_for_regular_member(self):
        perm = IsAdminOrReadOnly()
        request = make_request(method="POST", user=make_user(role="member"))
        assert perm.has_permission(request, None) is False


class TestIsOwnerOrAdmin:
    def test_unauthenticated_denied(self):
        perm = IsOwnerOrAdmin()
        request = make_request(user=make_user(is_authenticated=False))
        assert perm.has_permission(request, None) is False

    def test_superuser_allowed(self):
        perm = IsOwnerOrAdmin()
        request = make_request(user=make_user(is_superuser=True))
        assert perm.has_permission(request, None) is True

    def test_owner_allowed(self):
        perm = IsOwnerOrAdmin()
        request = make_request(user=make_user(is_owner=True))
        assert perm.has_permission(request, None) is True

    def test_admin_role_allowed(self):
        perm = IsOwnerOrAdmin()
        request = make_request(user=make_user(role="admin"))
        assert perm.has_permission(request, None) is True

    def test_regular_member_denied(self):
        perm = IsOwnerOrAdmin()
        request = make_request(user=make_user(role="member"))
        assert perm.has_permission(request, None) is False

    def test_object_permission_owner_created_by_match(self):
        perm = IsOwnerOrAdmin()
        user = make_user()
        request = make_request(user=user)
        obj = Mock(created_by=user)
        assert perm.has_object_permission(request, None, obj) is True

    def test_object_permission_denied_for_non_owner_non_creator(self):
        perm = IsOwnerOrAdmin()
        request = make_request(user=make_user())
        obj = Mock(created_by=Mock())
        assert perm.has_object_permission(request, None, obj) is False


class TestIsViewerOrHigher:
    def test_unauthenticated_denied(self):
        perm = IsViewerOrHigher()
        request = make_request(user=make_user(is_authenticated=False))
        assert perm.has_permission(request, None) is False

    def test_viewer_meets_default_required_level(self):
        perm = IsViewerOrHigher()
        request = make_request(user=make_user(role="viewer"))
        view = Mock(spec=[])
        assert perm.has_permission(request, view) is True

    def test_member_denied_when_admin_required(self):
        perm = IsViewerOrHigher()
        request = make_request(user=make_user(role="member"))
        view = Mock(required_role_level=3)
        assert perm.has_permission(request, view) is False

    def test_owner_flag_overrides_role_level(self):
        perm = IsViewerOrHigher()
        request = make_request(user=make_user(role="viewer", is_owner=True))
        view = Mock(required_role_level=4)
        assert perm.has_permission(request, view) is True


class TestCanInviteUsers:
    def test_admin_allowed(self):
        perm = CanInviteUsers()
        request = make_request(user=make_user(role="admin"))
        assert perm.has_permission(request, None) is True

    def test_member_denied(self):
        perm = CanInviteUsers()
        request = make_request(user=make_user(role="member"))
        assert perm.has_permission(request, None) is False


class TestCanManageBilling:
    def test_owner_allowed(self):
        perm = CanManageBilling()
        request = make_request(user=make_user(is_owner=True))
        assert perm.has_permission(request, None) is True

    def test_non_owner_denied(self):
        perm = CanManageBilling()
        request = make_request(user=make_user(is_owner=False, role="admin"))
        assert perm.has_permission(request, None) is False


class TestCanExportData:
    def test_viewer_denied(self):
        perm = CanExportData()
        request = make_request(user=make_user(role="viewer"))
        assert perm.has_permission(request, None) is False

    def test_member_allowed(self):
        perm = CanExportData()
        request = make_request(user=make_user(role="member"))
        assert perm.has_permission(request, None) is True


class TestIsSuperUser:
    def test_superuser_allowed(self):
        perm = IsSuperUser()
        request = make_request(user=make_user(is_superuser=True))
        assert perm.has_permission(request, None) is True

    def test_regular_user_denied(self):
        perm = IsSuperUser()
        request = make_request(user=make_user(is_superuser=False))
        assert perm.has_permission(request, None) is False


class TestReadOnly:
    def test_get_request_allowed(self):
        perm = ReadOnly()
        request = make_request(method="GET", user=make_user())
        assert perm.has_permission(request, None) is True

    def test_post_request_denied(self):
        perm = ReadOnly()
        request = make_request(method="POST", user=make_user())
        assert perm.has_permission(request, None) is False


class TestRateLimitExempt:
    def test_exempt_email_allowed(self):
        perm = RateLimitExempt()
        request = make_request(user=make_user(email="admin@example.com"))
        assert perm.has_permission(request, None) is True

    def test_exempt_ip_allowed(self):
        perm = RateLimitExempt()
        request = make_request(
            user=make_user(is_authenticated=False),
            meta={"REMOTE_ADDR": "127.0.0.1"},
        )
        assert perm.has_permission(request, None) is True

    def test_non_exempt_user_and_ip_denied(self):
        perm = RateLimitExempt()
        request = make_request(
            user=make_user(email="random@test.com"),
            meta={"REMOTE_ADDR": "203.0.113.5"},
        )
        assert perm.has_permission(request, None) is False

    def test_x_forwarded_for_takes_precedence(self):
        perm = RateLimitExempt()
        request = make_request(
            user=make_user(is_authenticated=False),
            meta={"HTTP_X_FORWARDED_FOR": "127.0.0.1, 10.20.30.40"},
        )
        assert perm.has_permission(request, None) is True


class TestOrganizationQuotaCheck:
    def test_unauthenticated_denied(self):
        perm = OrganizationQuotaCheck()
        request = make_request(user=make_user(is_authenticated=False))
        assert perm.has_permission(request, None) is False

    def test_no_organization_denied(self):
        perm = OrganizationQuotaCheck()
        request = make_request(user=make_user(organization=None))
        assert perm.has_permission(request, None) is False

    @patch("billing.utils.check_org_limit")
    def test_within_quota_allowed(self, mock_check):
        mock_check.return_value = True
        perm = OrganizationQuotaCheck()
        request = make_request(user=make_user())
        view = Mock(quota_resource="projects")
        assert perm.has_permission(request, view) is True

    @patch("billing.utils.check_org_limit")
    def test_over_quota_raises_permission_denied(self, mock_check):
        mock_check.return_value = False
        perm = OrganizationQuotaCheck()
        request = make_request(user=make_user())
        view = Mock(quota_resource="projects")
        with pytest.raises(PermissionDenied):
            perm.has_permission(request, view)


class TestIsVerifiedUser:
    def test_verified_user_allowed(self):
        perm = IsVerifiedUser()
        request = make_request(user=make_user(is_email_verified=True))
        assert perm.has_permission(request, None) is True

    def test_unverified_user_denied(self):
        perm = IsVerifiedUser()
        request = make_request(user=make_user(is_email_verified=False))
        assert perm.has_permission(request, None) is False


class TestTwoFactorRequired:
    def test_unauthenticated_denied(self):
        perm = TwoFactorRequired()
        request = make_request(user=make_user(is_authenticated=False))
        assert perm.has_permission(request, None) is False

    def test_superuser_bypasses_2fa(self):
        perm = TwoFactorRequired()
        request = make_request(user=make_user(is_superuser=True, two_factor_enabled=True))
        assert perm.has_permission(request, None) is True

    def test_2fa_disabled_allowed(self):
        perm = TwoFactorRequired()
        request = make_request(user=make_user(two_factor_enabled=False))
        assert perm.has_permission(request, None) is True

    def test_2fa_enabled_and_verified_in_session_allowed(self):
        perm = TwoFactorRequired()
        request = make_request(
            user=make_user(two_factor_enabled=True),
            session={"2fa_verified": True},
        )
        assert perm.has_permission(request, None) is True

    def test_2fa_enabled_but_not_verified_raises(self):
        perm = TwoFactorRequired()
        request = make_request(
            user=make_user(two_factor_enabled=True),
            session={},
        )
        with pytest.raises(PermissionDenied):
            perm.has_permission(request, None)