from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from organizations.models import Organization
from accounts.models import User


class OrgIntegrationTests(TestCase):

    def setUp(self):
        self.org = Organization.objects.create(name="Test Org")

        self.owner = User.objects.create_user(
            email="owner@test.com",
            password="pass123",
            organization=self.org,
            is_owner=True
        )

        self.client = APIClient()
        token = RefreshToken.for_user(self.owner).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_org_project_isolation_workflow(self):

        url = reverse("project-list")
        response = self.client.post(url, {"name": "Team Project"}, format="json")
        self.assertEqual(response.status_code, 201)

        project_id = response.data["id"]

     
        member = User.objects.create_user(
            email="member@test.com",
            password="pass123",
            organization=self.org,
            is_email_verified=True
        )

        member_client = APIClient()
        token = RefreshToken.for_user(member).access_token
        member_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

       
        response = member_client.get(url)
        self.assertEqual(response.status_code, 200)

  
        other_org = Organization.objects.create(name="Other Org")

        outsider = User.objects.create_user(
            email="outsider@test.com",
            password="pass123",
            organization=other_org
        )

        outsider_client = APIClient()
        token = RefreshToken.for_user(outsider).access_token
        outsider_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = outsider_client.get(url)

        self.assertEqual(len(response.data["results"]), 0)