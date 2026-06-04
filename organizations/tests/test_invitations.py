from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from organizations.models import Organization, OrganizationInvitation
from accounts.models import User


class InvitationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Test Org")
        self.owner = User.objects.create_user(
            email="inviteowner@example.com",
            password="pass123",
            organization=self.org,
            is_owner=True,
            is_email_verified=True,
        )
        refresh = RefreshToken.for_user(self.owner)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_invite_user(self):
        """Test inviting a user to organization"""
        url = reverse("invite")
        data = {"email": "invited@example.com"}


        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            OrganizationInvitation.objects.filter(email="invited@example.com").exists()
        )

    def test_accept_invitation(self):
        """Test accepting an invitation"""
        invitation = OrganizationInvitation.objects.create(
            organization=self.org,
            email="newuser@example.com",
            invited_by=self.owner,
            token="test_token_123",
        )

        new_user = User.objects.create_user(
            email="newuser@example.com",
            password="pass123",
            organization=self.org,
            is_email_verified=True,
        )

    
        new_client = APIClient()
        refresh = RefreshToken.for_user(new_user)
        new_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

        url = reverse("accept-invite", kwargs={"token": "test_token_123"})
        response = new_client.post(url, {"email": "newuser@example.com"}, format="json")
        self.assertEqual(response.status_code, 200)

        new_user.refresh_from_db()
        self.assertEqual(new_user.organization, self.org)
        invitation.refresh_from_db()
        self.assertTrue(invitation.accepted)
