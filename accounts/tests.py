from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from organizations.models import Organization

User = get_user_model()


class AccountModelTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Test Org")

    def test_create_user(self):
        user = User.objects.create_user(
            email="test@example.com", password="testpass123", organization=self.org
        )
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("testpass123"))

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            email="admin@example.com", password="admin123", organization=self.org
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_user_str_method(self):
        user = User.objects.create_user(
            email="str@example.com", password="test123", organization=self.org
        )
        self.assertEqual(str(user), "str@example.com")


class AccountAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = "/api/auth/register/"
        self.login_url = "/api/auth/login/"

    def test_register_user(self):
        data = {
            "email": "newuser@example.com",
            "password": "testpass123",
            "password2": "testpass123",
            "first_name": "John",
            "last_name": "Doe",
            "organization_name": "New Company",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)

    def test_register_duplicate_email(self):
        user = User.objects.create_user(
            email="duplicate@example.com", password="pass123"
        )
        data = {
            "email": "duplicate@example.com",
            "password": "testpass123",
            "password2": "testpass123",
            "organization_name": "Some Org",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        user = User.objects.create_user(
            email="login@example.com", password="correctpass"
        )
        data = {"email": "login@example.com", "password": "correctpass"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_login_invalid_password(self):
        user = User.objects.create_user(
            email="wrong@example.com", password="correctpass"
        )
        data = {"email": "wrong@example.com", "password": "wrongpass"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_user(self):
        data = {"email": "nonexistent@example.com", "password": "pass123"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_access(self):
        response = self.client.get("/api/projects/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
