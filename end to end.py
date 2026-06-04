from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from organizations.models import Organization
from projects.models import Project

User = get_user_model()


class SaasAPITest(TestCase):
    """
    Complete automation test suite for Multi-Tenant SaaS
    No manual intervention needed - runs automatically with Django test runner
    """

    def setUp(self):
        """Create fresh test data — isolated from your real database."""
        self.client = APIClient()

        self.org = Organization.objects.create(
            name="Test Company", plan="trial", subscription_status="active"
        )

        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            organization=self.org,
            is_owner=True,
            is_email_verified=True,
            is_active=True,
            role="admin",
        )

    def test_login_success(self):
        """Test successful login returns JWT tokens"""
        response = self.client.post(
            "/api/auth/login/",
            {"email": "test@example.com", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["email"], "test@example.com")

    def test_login_wrong_password(self):
        """Test login with wrong password fails"""
        response = self.client.post(
            "/api/auth/login/",
            {"email": "test@example.com", "password": "wrongpass"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_user(self):
        """Test login with non-existent email fails"""
        response = self.client.post(
            "/api/auth/login/",
            {"email": "nonexistent@example.com", "password": "pass"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_fields(self):
        """Test login with missing email/password"""
        response = self.client.post(
            "/api/auth/login/",
            {},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_organization_authenticated(self):
        """Test authenticated user can get organization details"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/organizations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Test Company")
        self.assertEqual(response.data["plan"], "trial")

    def test_get_organization_unauthenticated(self):
        """Test unauthenticated user cannot get organization"""
        response = self.client.get("/api/organizations/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_organization(self):
        """Test updating organization details"""
        self.client.force_authenticate(user=self.user)
        response = self.client.put(
            "/api/organizations/",
            {"name": "Updated Company", "plan": "basic"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.org.refresh_from_db()
        self.assertEqual(self.org.name, "Updated Company")
        self.assertEqual(self.org.plan, "basic")

    def test_create_project_authenticated(self):
        """Test authenticated user can create project"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/projects/",
            {"name": "Test Project", "description": "Testing all features"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Test Project")
        self.assertEqual(response.data["organization"], self.org.id)
        self.assertTrue(Project.objects.filter(name="Test Project").exists())

    def test_create_project_unauthenticated(self):
        """Test unauthenticated user cannot create project"""
        response = self.client.post(
            "/api/projects/",
            {"name": "Test Project", "description": "Testing all features"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_projects_authenticated(self):
        """Test authenticated user can list projects"""
        Project.objects.create(
            name="Project 1", organization=self.org, created_by=self.user
        )
        Project.objects.create(
            name="Project 2", organization=self.org, created_by=self.user
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/projects/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_get_project_detail(self):
        """Test getting single project details"""
        project = Project.objects.create(
            name="Detail Project", organization=self.org, created_by=self.user
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/projects/{project.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Detail Project")

    def test_update_project(self):
        """Test updating project"""
        project = Project.objects.create(
            name="Original Name", organization=self.org, created_by=self.user
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            f"/api/projects/{project.id}/",
            {"name": "Updated Name"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        project.refresh_from_db()
        self.assertEqual(project.name, "Updated Name")

    def test_delete_project(self):
        """Test deleting project"""
        project = Project.objects.create(
            name="To Delete", organization=self.org, created_by=self.user
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f"/api/projects/{project.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Project.objects.filter(id=project.id).exists())

    def test_dashboard_stats(self):
        """Test dashboard statistics endpoint"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/projects/dashboard/stats/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_projects", response.data)
        self.assertIn("organization_name", response.data)
        self.assertEqual(response.data["organization_name"], "Test Company")

    def test_realtime_dashboard(self):
        """Test real-time dashboard endpoint"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/dashboard/realtime/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("project_trends", response.data)
        self.assertIn("completion_rate", response.data)

    def test_create_task(self):
        """Test creating a task"""
        project = Project.objects.create(
            name="Task Project", organization=self.org, created_by=self.user
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/projects/tasks/",
            {"project": project.id, "title": "Test Task", "priority": "high"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Test Task")

    def test_create_comment(self):
        """Test creating a comment"""
        project = Project.objects.create(
            name="Comment Project", organization=self.org, created_by=self.user
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/comments/",
            {"project": project.id, "content": "Test comment"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["content"], "Test comment")

    def test_get_notifications(self):
        """Test getting notifications"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/notifications/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("notifications", response.data)

    def test_global_search(self):
        """Test global search functionality"""
        Project.objects.create(
            name="Searchable Project",
            description="This is a test project for search",
            organization=self.org,
            created_by=self.user,
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/search/global/?q=Searchable")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]["projects"]), 1)

    def test_search_no_query(self):
        """Test search without query parameter"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/search/global/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_export_projects_csv(self):
        """Test CSV export endpoint"""
        Project.objects.create(
            name="Export Project", organization=self.org, created_by=self.user
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/projects/export/projects/csv/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv")

    def test_tenant_isolation(self):
        """Test users from different orgs cannot see each other's data"""
        # Create another organization and user
        other_org = Organization.objects.create(name="Other Company")
        other_user = User.objects.create_user(
            email="other@example.com",
            password="pass123",
            organization=other_org,
            is_email_verified=True,
        )

        Project.objects.create(
            name="Org1 Project", organization=self.org, created_by=self.user
        )

        self.client.force_authenticate(user=other_user)
        response = self.client.get("/api/projects/")

        self.assertEqual(response.data["count"], 0)

    def test_member_cannot_update_others_project(self):
        """Test member cannot update project created by admin"""
        from accounts.models import User

        member_user = User.objects.create_user(
            email="member@example.com",
            password="pass123",
            organization=self.org,
            role="member",
            is_email_verified=True,
        )

        project = Project.objects.create(
            name="Admin Project",
            organization=self.org,
            created_by=self.user,  # Created by admin
        )

        self.client.force_authenticate(user=member_user)
        response = self.client.patch(
            f"/api/projects/{project.id}/",
            {"name": "Attempted Change"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
