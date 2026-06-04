from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from organizations.models import Organization
from accounts.models import User
from projects.models import Project, Task
from comments.models import Comment


class GlobalSearchTestCase(TestCase):
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
            name="Search Test Project",
            description="This project is for testing search",
            organization=self.org,
            created_by=self.user,
        )
        self.task = Task.objects.create(
            project=self.project, title="Search Test Task", created_by=self.user
        )
        self.comment = Comment.objects.create(
            project=self.project, user=self.user, content="Search test comment"
        )
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_global_search_finds_projects(self):
        """Test global search finds projects"""
        url = "/api/search/global/"
        response = self.client.get(url, {"q": "Search Test Project"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]["projects"]), 1)

    def test_global_search_finds_tasks(self):
        """Test global search finds tasks"""
        url = "/api/search/global/"
        response = self.client.get(url, {"q": "Search Test Task"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]["tasks"]), 1)

    def test_global_search_finds_comments(self):
        """Test global search finds comments"""
        url = "/api/search/global/"
        response = self.client.get(url, {"q": "search test comment"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]["comments"]), 1)

    def test_global_search_no_query(self):
        """Test global search without query parameter"""
        url = "/api/search/global/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Search query required", response.data["error"])

    def test_global_search_no_results(self):
        """Test global search with no matching results"""
        url = "/api/search/global/"
        response = self.client.get(url, {"q": "NonexistentQueryXYZ123"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]["projects"]), 0)
        self.assertEqual(len(response.data["results"]["tasks"]), 0)
        self.assertEqual(len(response.data["results"]["comments"]), 0)
