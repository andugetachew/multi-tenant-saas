from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Organization

User = get_user_model()


class OrganizationModelTests(TestCase):
    def test_create_organization(self):
        org = Organization.objects.create(name="Test Org", plan="trial")
        self.assertEqual(org.name, "Test Org")
        self.assertEqual(org.plan, "trial")

    def test_organization_str_method(self):
        org = Organization.objects.create(name="Acme Inc")
        self.assertEqual(str(org), "Acme Inc")


class OrganizationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Main Org")
        self.user = User.objects.create_user(
            email="user@example.com", password="pass123", organization=self.org
        )
        self.client.force_authenticate(user=self.user)

        # Manually set organization on request for tests
        self.client.defaults["HTTP_X_ORGANIZATION_ID"] = str(self.org.id)

    def test_get_organization(self):
        # Override the get_object method for testing
        response = self.client.get("/api/organizations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Main Org")

    def test_org_isolation(self):
        # Create another user in different org
        org2 = Organization.objects.create(name="Other Org")
        user2 = User.objects.create_user(
            email="other@example.com", password="pass123", organization=org2
        )

        self.client.force_authenticate(user=user2)
        self.client.defaults["HTTP_X_ORGANIZATION_ID"] = str(org2.id)

        response = self.client.get("/api/organizations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Other Org")
        self.assertNotEqual(response.data["name"], "Main Org")
