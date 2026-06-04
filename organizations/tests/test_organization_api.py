from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from organizations.models import Organization
from accounts.models import User


class OrganizationAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Test Org", plan="trial")
        self.user = User.objects.create_user(
            email="orgowner@example.com",  # ✅ changed from admin@example.com
            password="pass123",
            organization=self.org,
            is_owner=True,
            is_email_verified=True,
        )
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_get_organization_details(self):
        """Test retrieving organization details"""
        url = reverse("org-detail")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Test Org")
        self.assertEqual(response.data["plan"], "trial")

    def test_update_organization(self):
        """Test updating organization"""
        url = reverse("org-detail")
        data = {"name": "Updated Org Name", "plan": "basic"}
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.org.refresh_from_db()
        self.assertEqual(self.org.name, "Updated Org Name")
        self.assertEqual(self.org.plan, "basic")

    def test_unauthorized_access(self):
        """Test unauthorized access to organization"""
        client = APIClient()  # fresh client with no credentials
        url = reverse("org-detail")
        response = client.get(url)
        self.assertEqual(response.status_code, 401)
