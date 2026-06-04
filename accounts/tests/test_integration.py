from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from organizations.models import Organization

from django.test import override_settings

@override_settings(REST_FRAMEWORK={
    'DEFAULT_THROTTLE_CLASSES': [],
    'DEFAULT_THROTTLE_RATES': {}
})
class AuthIntegrationTests(TestCase):

    def test_complete_user_registration_flow(self):
        client = APIClient()
        register_url = reverse("register")
        register_data = {
            "email": "newuser@example.com",
            "password": "TestPass123!",
            "password2": "TestPass123!",
            "first_name": "New",
            "last_name": "User",
            "organization_name": "New Company",
        }
        response = client.post(register_url, register_data, format="json")
        self.assertEqual(response.status_code, 201)

        from accounts.models import User
        user = User.objects.get(email="newuser@example.com")
        user.is_email_verified = True
        user.is_active = True
        user.save()

        login_url = reverse("login")
        login_data = {
            "email": "newuser@example.com",
            "password": "TestPass123!",
        }
        response = client.post(login_url, login_data, format="json")
        self.assertEqual(response.status_code, 200)
        access_token = response.data["access"]

        profile_url = reverse("profile")
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = client.get(profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "newuser@example.com")
        self.assertTrue(
            Organization.objects.filter(name="New Company").exists()
        )