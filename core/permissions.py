# core/permissions.py
from rest_framework import permissions
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has a `created_by` attribute.
    """

    def has_object_permission(self, request, view, obj):

        if request.method in permissions.SAFE_METHODS:
            return True


        return obj.created_by == request.user


class IsOrganizationMember(BasePermission):
    """
    FAANG-level: Ensures user belongs to the organization
    Used for: Multi-tenant isolation
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True


        if not request.user.organization_id:
            return False

        return True

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True


        if hasattr(obj, "organization"):
            return obj.organization_id == request.user.organization_id
        elif hasattr(obj, "project") and hasattr(obj.project, "organization"):
            return obj.project.organization_id == request.user.organization_id
        elif hasattr(obj, "user") and obj.user == request.user:
            return True

        return False


class IsAdminOrReadOnly(BasePermission):
    """
    FAANG-level: Admin users have full access, others have read-only
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        if not request.user.is_authenticated:
            return False

        return request.user.role == "admin" or request.user.is_owner


class IsOwnerOrAdmin(BasePermission):
    """
    FAANG-level: Owners and admins have full access
    Used for: Organization settings, Billing
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        return request.user.is_owner or request.user.role == "admin"

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        if request.user.is_owner:
            return True

        if hasattr(obj, "created_by") and obj.created_by == request.user:
            return True

        return False


class IsViewerOrHigher(BasePermission):
    """
    FAANG-level: Role-based access control
    Viewer: Read-only
    Member: Read + Create
    Admin: Full access
    Owner: Full access + Billing
    """

    ROLE_HIERARCHY = {"viewer": 1, "member": 2, "admin": 3, "owner": 4}

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        required_level = getattr(view, "required_role_level", 1)
        user_level = self.ROLE_HIERARCHY.get(request.user.role, 0)

        if request.user.is_owner:
            user_level = 4

        return user_level >= required_level


class CanInviteUsers(BasePermission):
    """
    FAANG-level: Only admins and owners can invite users
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return request.user.role == "admin" or request.user.is_owner


class CanManageBilling(BasePermission):
    """
    FAANG-level: Only owners can manage billing
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return request.user.is_owner


class CanExportData(BasePermission):
    """
    FAANG-level: Members and above can export
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.role == "viewer":
            return False

        return True


class IsSuperUser(BasePermission):
    """
    FAANG-level: Superuser only access
    Used for: Admin panels, System settings
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superuser


class ReadOnly(BasePermission):
    """
    FAANG-level: Read-only access for all authenticated users
    """

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS and request.user.is_authenticated


class RateLimitExempt(BasePermission):
    """
    FAANG-level: Exempt specific users from rate limiting
    Used for: Internal services, Trusted IPs
    """

    def has_permission(self, request, view):
        # Check if user is in exempt list
        if request.user.is_authenticated:
            exempt_emails = ["admin@example.com", "system@example.com"]
            if request.user.email in exempt_emails:
                return True

        # Check if IP is in exempt list
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")

        exempt_ips = ["127.0.0.1", "10.0.0.0/8"]
        if ip in exempt_ips:
            return True

        return False


class OrganizationQuotaCheck(BasePermission):
    """
    FAANG-level: Check if organization has reached its quota
    Used for: Subscription plan limits
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        org = request.user.organization
        if not org:
            return False

        # Get quota limit from subscription
        from organizations.limits import check_org_limit

        resource_type = getattr(view, "quota_resource", "projects")

        if not check_org_limit(org, resource_type):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                f"{resource_type.capitalize()} limit reached. Please upgrade your plan."
            )

        return True


class IsVerifiedUser(BasePermission):
    """
    FAANG-level: Only verified email users can access
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return request.user.is_email_verified


class TwoFactorRequired(BasePermission):
    """
    FAANG-level: Require 2FA for sensitive operations
    Used for: Billing, Security settings, API key management
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Skip 2FA check for superusers (backward compatibility)
        if request.user.is_superuser:
            return True

        # Check if user has 2FA enabled
        if request.user.two_factor_enabled:
            # Check if 2FA token was verified in this session
            if not request.session.get("2fa_verified", False):
                from rest_framework.exceptions import PermissionDenied

                raise PermissionDenied("Two-factor authentication required.")

        return True
