from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from organizations.models import Organization
from django.conf import settings
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    EmailVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)

from core.rate_limits import (
    AuthLoginThrottle,
    AuthRegisterThrottle,
    AuthPasswordResetThrottle,
    AuthVerifyEmailThrottle,
)

from tasks.email_tasks import (
    send_verification_email_task,
    send_password_reset_email_task,
)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer
    throttle_classes = [AuthRegisterThrottle]

    def perform_create(self, serializer):
        user = serializer.save()

        token = user.generate_email_verification_token()

        verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        send_verification_email_task.delay(user.email, verification_link)

        return user


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthLoginThrottle]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=401)

        # Check if email is verified
        if not user.is_email_verified:
            return Response(
                {"error": "Please verify your email first. Check your inbox."},
                status=401,
            )

        if not user.check_password(password):
            return Response({"error": "Invalid credentials"}, status=401)

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "organization": user.organization_id,
                    "is_owner": user.is_owner,
                    "is_email_verified": user.is_email_verified,
                },
            }
        )


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthVerifyEmailThrottle]

    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]

        try:
            user = User.objects.get(email_verification_token=token)
        except User.DoesNotExist:
            return Response({"error": "Invalid or expired token"}, status=400)

        # Check if token is expired (24 hours)
        if user.email_verification_sent_at:
            from django.utils import timezone

            expiry = user.email_verification_sent_at + timezone.timedelta(hours=24)
            if timezone.now() > expiry:
                return Response(
                    {"error": "Token expired. Request a new verification email."},
                    status=400,
                )

        user.is_email_verified = True
        user.is_active = True
        user.email_verification_token = None
        user.save()

        return Response({"message": "Email verified successfully. You can now login."})


class ResendVerificationEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        if user.is_email_verified:
            return Response({"message": "Email already verified"}, status=400)

        token = user.generate_email_verification_token()
        verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        send_verification_email_task.delay(user.email, verification_link)
        return Response({"message": "Verification email sent"})


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthPasswordResetThrottle]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Return success even if user doesn't exist (security)
            return Response(
                {"message": "If an account exists, a reset link has been sent."}
            )

        token = user.generate_password_reset_token()
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        send_password_reset_email_task.delay(user.email, reset_link)

        return Response({"message": "Password reset link sent to your email"})


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        try:
            user = User.objects.get(password_reset_token=token)
        except User.DoesNotExist:
            return Response({"error": "Invalid or expired token"}, status=400)

        if not user.is_password_reset_token_valid():
            return Response(
                {"error": "Token expired. Request a new password reset."}, status=400
            )

        user.set_password(new_password)
        user.password_reset_token = None
        user.password_reset_token_created_at = None
        user.save()

        return Response({"message": "Password reset successfully"})


class TestLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        if not user.check_password(password):
            return Response({"error": "Wrong password"}, status=401)

        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "organization": user.organization_id,
                },
            }
        )
