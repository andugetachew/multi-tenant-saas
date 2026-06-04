from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from organizations.models import Organization
from accounts.models import User
from notifications.models import Notification


class NotificationAPITestCase(TestCase):
    """Test notification API (multi-tenant safe)"""

    def setUp(self):
        self.client = APIClient()

        self.org = Organization.objects.create(name="Test Org")
        self.other_org = Organization.objects.create(name="Other Org")

        self.user = User.objects.create_user(
            email="user@example.com",
            password="pass123",
            organization=self.org,
            is_email_verified=True,
        )

        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="pass123",
            organization=self.other_org,
            is_email_verified=True,
        )

        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")



    def test_list_notifications(self):
        Notification.objects.create(
            user=self.user,
            title="Test Notification",
            message="Test message",
            notification_type="info",
            is_read=False,
        )

        response = self.client.get("/api/notifications/")

        self.assertEqual(response.status_code, 200)

   
        self.assertTrue(
            any(n["title"] == "Test Notification"
                for n in response.data.get("notifications", []))
        )

    

    def test_mark_all_read(self):
        Notification.objects.create(
            user=self.user,
            title="N1",
            message="Msg",
            is_read=False,
        )
        Notification.objects.create(
            user=self.user,
            title="N2",
            message="Msg",
            is_read=False,
        )

        response = self.client.post("/api/notifications/mark-all-read/")

        self.assertEqual(response.status_code, 200)

        unread_count = Notification.objects.filter(
            user=self.user,
            is_read=False
        ).count()

        self.assertEqual(unread_count, 0)

    

    def test_user_cannot_see_other_org_notifications(self):
        Notification.objects.create(
            user=self.other_user,
            title="Other Org Notification",
            message="Hidden",
            is_read=False,
        )

        response = self.client.get("/api/notifications/")

        self.assertEqual(response.status_code, 200)

        titles = [n["title"] for n in response.data.get("notifications", [])]

        self.assertNotIn("Other Org Notification", titles)