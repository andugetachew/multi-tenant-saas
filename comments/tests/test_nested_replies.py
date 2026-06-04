from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from organizations.models import Organization
from accounts.models import User
from projects.models import Project
from comments.models import Comment


class NestedRepliesTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Test Org")
        self.user = User.objects.create_user(
            email="user@example.com",
            password="pass123",
            organization=self.org,
            is_email_verified=True,
        )
        self.project = Project.objects.create(
            name="Test Project", organization=self.org, created_by=self.user
        )
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_create_reply(self):
        """Test creating a reply to a comment"""
        parent_comment = Comment.objects.create(
            project=self.project, user=self.user, content="Parent comment"
        )

        url = "/api/comments/"
        data = {
            "project": self.project.id,
            "content": "Reply comment",
            "parent": parent_comment.id,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["parent"], parent_comment.id)

    def test_comment_replies_nested(self):
        """Test that replies are nested under parent comments"""
        parent = Comment.objects.create(
            project=self.project, user=self.user, content="Parent"
        )
        reply = Comment.objects.create(
            project=self.project, user=self.user, content="Reply", parent=parent
        )

        url = "/api/comments/"
        response = self.client.get(url, {"project_id": self.project.id})

        # Find parent comment in response
        parent_in_response = None
        for comment in response.data["results"]:
            if comment["id"] == parent.id:
                parent_in_response = comment
                break

        self.assertIsNotNone(parent_in_response)
        self.assertEqual(len(parent_in_response["replies"]), 1)
        self.assertEqual(parent_in_response["replies"][0]["id"], reply.id)
