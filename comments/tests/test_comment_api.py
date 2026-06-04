from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from organizations.models import Organization
from accounts.models import User
from projects.models import Project
from comments.models import Comment


class CommentAPITestCase(TestCase):
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

    def test_create_comment(self):
        """Test creating a comment"""
        url = reverse("comment-list")
        data = {"project": self.project.id, "content": "This is a test comment"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["content"], "This is a test comment")

    def test_list_comments(self):
        """Test listing comments"""
        Comment.objects.create(
            project=self.project, user=self.user, content="Comment 1"
        )
        Comment.objects.create(
            project=self.project, user=self.user, content="Comment 2"
        )

        url = reverse("comment-list")
        response = self.client.get(url, {"project_id": self.project.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)

    def test_delete_comment(self):
        """Test deleting a comment"""
        comment = Comment.objects.create(
            project=self.project, user=self.user, content="To Delete"
        )
        url = reverse("comment-detail", kwargs={"pk": comment.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Comment.objects.filter(id=comment.id).exists())
