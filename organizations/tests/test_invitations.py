import pytest
import secrets
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from organizations.models import Organization, OrganizationInvitation
from accounts.models import User
from django.db import IntegrityError


# ─────────────────────────────────────────────────────────
# EXISTING TESTS (unchanged)
# ─────────────────────────────────────────────────────────

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
        url = reverse("invite")
        data = {"email": "invited@example.com"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            OrganizationInvitation.objects.filter(email="invited@example.com").exists()
        )

    def test_accept_invitation(self):
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


# ─────────────────────────────────────────────────────────
# ADDED: INVITE CREATION FAILURE PATHS
# ─────────────────────────────────────────────────────────

class InviteCreationFailuresTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Failure Org")
        self.owner = User.objects.create_user(
            email="owner2@test.com",
            password="StrongPass123!",
            organization=self.org,
            is_owner=True,
            is_email_verified=True,
            is_active=True,
        )
        self.member = User.objects.create_user(
            email="member@test.com",
            password="StrongPass123!",
            organization=self.org,
            is_owner=False,
            role="member",
            is_email_verified=True,
            is_active=True,
        )
        # pending invitation for duplicate test
        self.pending = OrganizationInvitation.objects.create(
            organization=self.org,
            email="newguy@test.com",
            invited_by=self.owner,
            token=secrets.token_hex(32),
            accepted=False,
        )

    def test_member_cannot_invite(self):
        self.client.force_authenticate(user=self.member)
        r = self.client.post("/api/organizations/invite/", {
            "email": "newcomer@test.com"
        }, format="json")
        self.assertIn(r.status_code, [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_401_UNAUTHORIZED,
        ])

    def test_unauthenticated_cannot_invite(self):
        r = self.client.post("/api/organizations/invite/", {
            "email": "ghost@test.com"
        }, format="json")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_email_format_returns_400(self):
        self.client.force_authenticate(user=self.owner)
        r = self.client.post("/api/organizations/invite/", {
            "email": "not-an-email"
        }, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_email_field_returns_400(self):
        self.client.force_authenticate(user=self.owner)
        r = self.client.post("/api/organizations/invite/", {}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_invitation_rejected(self):
        self.client.force_authenticate(user=self.owner)
        r = self.client.post("/api/organizations/invite/", {
            "email": "newguy@test.com"  # same as self.pending
        }, format="json")
        self.assertIn(r.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_409_CONFLICT,
        ])


# ─────────────────────────────────────────────────────────
# ADDED: INVITE ACCEPTANCE FAILURE PATHS
# ─────────────────────────────────────────────────────────

class InviteAcceptanceFailuresTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Accept Org")
        self.owner = User.objects.create_user(
            email="owner3@test.com",
            password="pass123",
            organization=self.org,
            is_owner=True,
            is_email_verified=True,
            is_active=True,
        )
        self.accepted = OrganizationInvitation.objects.create(
            organization=self.org,
            email="alreadyin@test.com",
            invited_by=self.owner,
            token=secrets.token_hex(32),
            accepted=True,
        )

    def test_invalid_token_returns_404(self):
        fake_token = secrets.token_hex(32)
        r = self.client.post(
            f"/api/organizations/invitations/{fake_token}/accept/"
        )
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)

    def test_already_accepted_invitation_rejected(self):
        r = self.client.post(
            f"/api/organizations/invitations/{self.accepted.token}/accept/"
        )
        self.assertIn(r.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_410_GONE,
        ])


# ─────────────────────────────────────────────────────────
# ADDED: MODEL EDGE CASES
# ─────────────────────────────────────────────────────────

class OrganizationInvitationModelTestCase(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Model Org")
        self.owner = User.objects.create_user(
            email="owner4@test.com",
            password="pass123",
            organization=self.org,
            is_owner=True,
            is_email_verified=True,
        )

    def test_token_must_be_unique(self):
        token = secrets.token_hex(32)
        OrganizationInvitation.objects.create(
            organization=self.org, email="first@test.com", token=token
        )
        with self.assertRaises(Exception):
            OrganizationInvitation.objects.create(
                organization=self.org, email="second@test.com", token=token
            )

    def test_cascade_delete_with_org(self):
        OrganizationInvitation.objects.create(
            organization=self.org,
            email="cascade@test.com",
            token=secrets.token_hex(32),
        )
        org_id = self.org.pk
        self.org.delete()
        self.assertEqual(
            OrganizationInvitation.objects.filter(organization_id=org_id).count(), 0
        )

    def test_invited_by_set_null_on_user_delete(self):
        inv = OrganizationInvitation.objects.create(
            organization=self.org,
            email="orphan@test.com",
            invited_by=self.owner,
            token=secrets.token_hex(32),
        )
        self.owner.delete()
        inv.refresh_from_db()
        self.assertIsNone(inv.invited_by)