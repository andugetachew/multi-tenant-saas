from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user


from rest_framework import permissions


class IsAdminOrOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Admins and owners can do everything
        if request.user.role == "admin" or request.user.is_owner:
            return True

        # Viewers can only read (GET, HEAD, OPTIONS)
        if request.user.role == "viewer":
            return request.method in permissions.SAFE_METHODS

        # Members can read and create but not delete/update others
        if request.user.role == "member":
            if request.method in ["POST", "GET", "HEAD", "OPTIONS"]:
                return True

        return False

    def has_object_permission(self, request, view, obj):
        # Owners and admins can do anything
        if request.user.is_owner or request.user.role == "admin":
            return True

        # Users can modify their own objects
        if hasattr(obj, "created_by") and obj.created_by == request.user:
            return True

        # Viewers read only
        if request.user.role == "viewer":
            return request.method in permissions.SAFE_METHODS

        return False
