from django.urls import path
from .views import LoginView
from .views import TestLoginView
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView,
    LoginView,
    VerifyEmailView,
    ResendVerificationEmailView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    LogoutView,
    UserProfileView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path(
        "resend-verification/",
        ResendVerificationEmailView.as_view(),
        name="resend-verification",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", UserProfileView.as_view(), name="profile"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "forgot-password/", PasswordResetRequestView.as_view(), name="forgot-password"
    ),
    path(
        "reset-password/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(),
        name="reset-password",
    ),
    path("test-login/", TestLoginView.as_view(), name="test-login"),
]
