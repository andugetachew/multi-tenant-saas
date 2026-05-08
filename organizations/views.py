# organizations/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Organization, OrganizationInvitation
from .serializers import OrganizationSerializer, OrganizationInvitationSerializer
from accounts.models import User
import secrets


class OrganizationDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Try to get from request, then from user, then return 404
        org = getattr(self.request, "organization", None)
        if not org and self.request.user.is_authenticated:
            org = self.request.user.organization

        if not org:
            return Response(
                {"error": "Organization not found"}, status=status.HTTP_404_NOT_FOUND
            )
        return org


class InviteUserView(generics.CreateAPIView):
    serializer_class = OrganizationInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer(self, *args, **kwargs):
        # Remove organization from request data
        if isinstance(kwargs.get("data"), dict):
            data = kwargs["data"].copy()
            data.pop("organization", None)
            kwargs["data"] = data
        return super().get_serializer(*args, **kwargs)

    def perform_create(self, serializer):
        token = secrets.token_urlsafe(32)
        serializer.save(
            organization=self.request.user.organization,
            invited_by=self.request.user,
            token=token,
        )


class AcceptInvitationView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, token):
        try:
            inv = OrganizationInvitation.objects.get(token=token, accepted=False)
        except OrganizationInvitation.DoesNotExist:
            return Response(
                {"error": "Invalid invitation"}, status=status.HTTP_400_BAD_REQUEST
            )

        user_email = request.data.get("email")
        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found. Please register first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.organization = inv.organization
        user.save()
        inv.accepted = True
        inv.save()
        return Response({"message": "Invitation accepted"}, status=status.HTTP_200_OK)
