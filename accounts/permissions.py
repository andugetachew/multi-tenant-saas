from rest_framework import permissions
from rest_framework.exceptions import NotFound

class IsAdminOrOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.role == "admin" or request.user.is_owner:
            return True

        if request.user.role == "viewer":
            return request.method in permissions.SAFE_METHODS

        if request.user.role == "member":
            if request.method in ["POST", "GET", "HEAD", "OPTIONS"]:
                return True

        return False

    def has_object_permission(self, request, view, obj):

        if hasattr(obj, 'organization') and obj.organization != request.user.organization:
            raise NotFound(detail="Not found.")
        
        if request.method == 'DELETE':
            if hasattr(obj, 'created_by') and obj.created_by == request.user:
                return True
            if request.user.is_owner or request.user.role == "admin":
                return True
            return False
        
        if request.method in ['PUT', 'PATCH']:
            if hasattr(obj, 'created_by') and obj.created_by == request.user:
                return True
            if request.user.is_owner or request.user.role == "admin":
                return True
            return False
            
        if request.user.is_owner or request.user.role == "admin":
            return True

        if request.user.role == "viewer":
            return request.method in permissions.SAFE_METHODS

        if request.user.role == "member":
            if hasattr(obj, "created_by") and obj.created_by == request.user:
                return True
            if hasattr(obj, "user") and obj.user == request.user:
                return True

        return False