import pytest
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import User
from organizations.models import Organization
from unittest.mock import patch


# ─────────────────────────────────────────────────────────
# EXISTING TESTS (unchanged)
# ─────────────────────────────────────────────────────────

class AuthTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Test Org", plan="basic")

    @patch('tasks.email_tasks.send_verification_email_task.delay')
    def test_register_success(self, mock_task):
        url = reverse("register")
        data = {
            "email": "newuser@example.com",
            "password": "TestPass123!",
            "password2": "TestPass123!",
            "first_name": "John",
            "last_name": "Doe",
            "organization_name": "New Company",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="newuser@example.com").exists())

    def test_register_password_mismatch(self):
        url = reverse("register")
        data = {
            "email": "newuser@example.com",
            "password": "pass123",
            "password2": "different",
            "organization_name": "Company",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            organization=self.org,
            is_email_verified=True,
            is_active=True,
        )
        url = reverse("login")
        data = {"email": "test@example.com", "password": "testpass123"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_invalid_credentials(self):
        url = reverse("login")
        data = {"email": "wrong@example.com", "password": "wrongpass"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_unverified_email(self):
        user = User.objects.create_user(
            email="unverified@example.com",
            password="pass123",
            organization=self.org,
            is_email_verified=False,
        )
        url = reverse("login")
        data = {"email": "unverified@example.com", "password": "pass123"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("verify your email", response.data["error"].lower())


class TokenRefreshTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Test Org")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            organization=self.org,
            is_email_verified=True,
        )

    def test_refresh_token(self):
        login_url = reverse("login")
        response = self.client.post(
            login_url,
            {"email": "test@example.com", "password": "testpass123"},
            format="json",
        )
        refresh_token = response.data["refresh"]
        refresh_url = reverse("token_refresh")
        response = self.client.post(
            refresh_url, {"refresh": refresh_token}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)


# ─────────────────────────────────────────────────────────
# ADDED: LOGOUT
# ─────────────────────────────────────────────────────────

class LogoutTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Logout Org")
        self.user = User.objects.create_user(
            email="logout@test.com",
            password="StrongPass123!",
            organization=self.org,
            is_email_verified=True,
            is_active=True,
        )

    def _get_tokens(self):
        response = self.client.post(reverse("login"), {
            "email": self.user.email,
            "password": "StrongPass123!"
        }, format="json")
        return response.data["refresh"]

    def test_valid_refresh_token_logs_out(self):
        refresh = self._get_tokens()
        self.client.force_authenticate(user=self.user)
        r = self.client.post("/api/auth/logout/", {"refresh": refresh}, format="json")
        self.assertEqual(r.status_code, status.HTTP_205_RESET_CONTENT)

    def test_invalid_token_returns_400(self):
        self.client.force_authenticate(user=self.user)
        r = self.client.post("/api/auth/logout/", {"refresh": "bad.token"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_returns_401(self):
        r = self.client.post("/api/auth/logout/", {"refresh": "token"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)


# ─────────────────────────────────────────────────────────
# ADDED: EMAIL VERIFICATION
# ─────────────────────────────────────────────────────────

class EmailVerificationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Verify Org")
        self.user = User.objects.create_user(
            email="unverified@test.com",
            password="StrongPass123!",
            organization=self.org,
            is_email_verified=False,
            is_active=False,
        )
        self.user.generate_email_verification_token()

    def test_valid_token_verifies_user(self):
        r = self.client.post("/api/auth/verify-email/", {
            "token": self.user.email_verification_token
        }, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)

    def test_invalid_token_returns_400(self):
        r = self.client.post("/api/auth/verify-email/", {
            "token": "fake-token-xyz"
        }, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_expired_token_returns_400(self):
        self.user.email_verification_sent_at = (
            timezone.now() - timezone.timedelta(hours=25)
        )
        self.user.save()
        r = self.client.post("/api/auth/verify-email/", {
            "token": self.user.email_verification_token
        }, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("expired", r.data.get("error", "").lower())

    def test_missing_token_field_returns_400(self):
        r = self.client.post("/api/auth/verify-email/", {}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────────────────
# ADDED: RESEND VERIFICATION
# ─────────────────────────────────────────────────────────

class ResendVerificationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Resend Org")
        self.verified_user = User.objects.create_user(
            email="verified@test.com",
            password="StrongPass123!",
            organization=self.org,
            is_email_verified=True,
            is_active=True,
        )
        self.unverified_user = User.objects.create_user(
            email="unverified2@test.com",
            password="StrongPass123!",
            organization=self.org,
            is_email_verified=False,
            is_active=False,
        )

    def test_resend_to_unverified_user(self):
        r = self.client.post("/api/auth/resend-verification/", {
            "email": self.unverified_user.email
        }, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_already_verified_returns_400(self):
        r = self.client.post("/api/auth/resend-verification/", {
            "email": self.verified_user.email
        }, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already verified", r.data.get("message", "").lower())

    def test_nonexistent_email_returns_404(self):
        r = self.client.post("/api/auth/resend-verification/", {
            "email": "nobody@nowhere.com"
        }, format="json")
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)


# ─────────────────────────────────────────────────────────
# ADDED: PASSWORD RESET
# ─────────────────────────────────────────────────────────

class PasswordResetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Reset Org")
        self.user = User.objects.create_user(
            email="reset@test.com",
            password="StrongPass123!",
            organization=self.org,
            is_email_verified=True,
            is_active=True,
        )

    def test_nonexistent_email_still_returns_200(self):
        r = self.client.post("/api/auth/password-reset/", {
            "email": "ghost@nowhere.com"
        }, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_invalid_email_format_returns_400(self):
        r = self.client.post("/api/auth/password-reset/", {
            "email": "not-an-email"
        }, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_valid_email_sets_reset_token(self):
        self.client.post("/api/auth/password-reset/", {
            "email": self.user.email
        }, format="json")
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.password_reset_token)

    def test_invalid_reset_token_returns_400(self):
        r = self.client.post("/api/auth/password-reset/confirm/", {
            "token": "fake-token",
            "new_password": "NewPass999!"
        }, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_expired_reset_token_returns_400(self):
        self.user.generate_password_reset_token()
        self.user.password_reset_token_created_at = (
            timezone.now() - timezone.timedelta(hours=25)
        )
        self.user.save()
        r = self.client.post("/api/auth/password-reset/confirm/", {
            "token": self.user.password_reset_token,
            "new_password": "NewPass999!"
        }, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("expired", r.data.get("error", "").lower())

    def test_valid_token_resets_password(self):
        self.user.generate_password_reset_token()
        r = self.client.post("/api/auth/password-reset/confirm/", {
            "token": self.user.password_reset_token,
            "new_password": "NewPass999!"
        }, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.password_reset_token)

    def test_new_password_works_for_login(self):
        self.user.generate_password_reset_token()
        new_password = "BrandNew999!"
        self.client.post("/api/auth/password-reset/confirm/", {
            "token": self.user.password_reset_token,
            "new_password": new_password
        }, format="json")
        r = self.client.post(reverse("login"), {
            "email": self.user.email,
            "password": new_password
        }, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────
# ADDED: USER PROFILE
# ─────────────────────────────────────────────────────────

class UserProfileTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Profile Org")
        self.user = User.objects.create_user(
            email="profile@test.com",
            password="StrongPass123!",
            organization=self.org,
            is_email_verified=True,
            is_active=True,
        )

    def test_get_own_profile(self):
        self.client.force_authenticate(user=self.user)
        r = self.client.get("/api/auth/profile/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["email"], self.user.email)

    def test_unauthenticated_returns_401(self):
        r = self.client.get("/api/auth/profile/")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_valid_field(self):
        self.client.force_authenticate(user=self.user)
        r = self.client.patch("/api/auth/profile/", {
            "first_name": "Updated"
        }, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")

    def test_patch_duplicate_email_returns_400(self):
        other = User.objects.create_user(
            email="taken@test.com", password="pass",
            organization=self.org, is_active=True,
        )
        self.client.force_authenticate(user=self.user)
        r = self.client.patch("/api/auth/profile/", {
            "email": other.email
        }, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)