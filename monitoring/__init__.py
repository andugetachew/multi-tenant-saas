# accounts/tests/test_auth.py
import pytest
from django.urls import reverse
from rest_framework import status
from accounts.models import User

pytestmark = pytest.mark.django_db


class TestAuthentication:

    def test_register_success(self, api_client):
        """Test user registration"""
        url = reverse("register")
        data = {
            "email": "newuser@example.com",
            "password": "TestPass123!",
            "password2": "TestPass123!",
            "first_name": "John",
            "last_name": "Doe",
            "organization_name": "New Company",
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(email="newuser@example.com").exists()

    def test_login_success(self, api_client, test_user):
        """Test login with valid credentials"""
        url = reverse("login")
        data = {"email": "test@example.com", "password": "testpass123"}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_invalid_password(self, api_client, test_user):
        """Test login with wrong password"""
        url = reverse("login")
        data = {"email": "test@example.com", "password": "wrongpass"}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_unverified_email(self, api_client):
        """Test login with unverified email"""
        org = Organization.objects.create(name="Test Org")
        user = User.objects.create_user(
            email="unverified@example.com",
            password="pass123",
            organization=org,
            is_email_verified=False,
        )
        url = reverse("login")
        data = {"email": "unverified@example.com", "password": "pass123"}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
