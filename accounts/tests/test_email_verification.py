from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User
from organizations.models import Organization
from unittest.mock import patch


class EmailVerificationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Test Org")

    @patch("tasks.email_tasks.send_verification_email_task.delay")
    def test_register_sends_verification_email(self, mock_send_email):
        """Test that registration sends verification email"""
        url = reverse("register")
        data = {
            "email": "test@example.com",
            "password": "TestPass123!",
            "password2": "TestPass123!",
            "first_name": "Test",
            "last_name": "User",
            "organization_name": "Test Org",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_send_email.assert_called_once()

    def test_verify_email_success(self):
        """Test successful email verification"""
        user = User.objects.create_user(
            email="test@example.com",
            password="pass123",
            organization=self.org,
            is_email_verified=False,
            is_active=False,
        )
        token = user.generate_email_verification_token()

        url = reverse("verify-email")
        response = self.client.post(url, {"token": token}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)
        self.assertTrue(user.is_active)

    def test_verify_email_invalid_token(self):
        """Test verification with invalid token"""
        url = reverse("verify-email")
        response = self.client.post(url, {"token": "invalid_token"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_resend_verification_email(self):
        """Test resending verification email"""
        user = User.objects.create_user(
            email="test@example.com",
            password="pass123",
            organization=self.org,
            is_email_verified=False,
        )
        url = reverse("resend-verification")
        response = self.client.post(url, {"email": "test@example.com"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
