from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User
from organizations.models import Organization


class AuthTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Test Org", plan="basic")

    from unittest.mock import patch

    @patch('celery.current_app.send_task')
    @patch('accounts.tasks.send_welcome_email_task.delay')
    def test_register_success(self):
        """Test user registration with organization creation"""
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
        """Test registration with mismatched passwords"""
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
        """Test successful login with verified email"""
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
        """Test login with invalid credentials"""
        url = reverse("login")
        data = {"email": "wrong@example.com", "password": "wrongpass"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_unverified_email(self):
        """Test login with unverified email"""
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
        """Test token refresh endpoint"""
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
