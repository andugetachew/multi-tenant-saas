from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Organization, OrganizationInvitation
from .serializers import OrganizationSerializer, OrganizationInvitationSerializer
from accounts.models import User
import secrets
from notifications.utils import create_notification
from core.rate_limits import OrgInviteThrottle, OrgCreateThrottle, OrgUpdateThrottle


class OrganizationDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [OrgUpdateThrottle]

    def get_object(self):
        org = getattr(self.request, "organization", None)
        if not org and self.request.user.is_authenticated:
            org = self.request.user.organization
        if not org:
            from rest_framework.exceptions import NotFound
            raise NotFound("Organization not found")
        return org


class InviteUserView(generics.CreateAPIView):
    serializer_class = OrganizationInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [OrgInviteThrottle]

    def get_serializer(self, *args, **kwargs):
        if isinstance(kwargs.get("data"), dict):
            data = kwargs["data"].copy()
            data.pop("organization", None)
            kwargs["data"] = data
        return super().get_serializer(*args, **kwargs)

    def perform_create(self, serializer):
        if not self.request.user.is_owner:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only organization owners can invite users.")

        org = (
            getattr(self.request, "organization", None)
            or self.request.user.organization
        )

        email = serializer.validated_data.get("email")

        if OrganizationInvitation.objects.filter(
            organization=org, email=email, accepted=False
        ).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError("An invitation has already been sent to this email.")

        token = secrets.token_urlsafe(32)
        invitation = serializer.save(
            organization=org,
            invited_by=self.request.user,
            token=token,
        )
        create_notification(
            user=self.request.user,
            title="Invitation Sent",
            message=f"Invitation sent to {invitation.email}",
            notification_type="success",
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


class OrganizationCreateView(generics.CreateAPIView):
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [OrgCreateThrottle]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
