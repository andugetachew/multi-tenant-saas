from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from organizations.models import Organization
from accounts.models import User
from projects.models import Project, Task


class ProjectPermissionTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Test Org", plan="trial")
        
       
        self.admin = User.objects.create_user(
            email="admin@test.com",
            password="pass123",
            organization=self.org,
            role="admin",
            is_owner=False
        )
        
        self.member = User.objects.create_user(
            email="member@test.com",
            password="pass123",
            organization=self.org,
            role="member",
            is_owner=False
        )
        
        self.viewer = User.objects.create_user(
            email="viewer@test.com",
            password="pass123",
            organization=self.org,
            role="viewer",
            is_owner=False
        )
        
        self.owner = User.objects.create_user(
            email="owner@test.com",
            password="pass123",
            organization=self.org,
            role="admin",
            is_owner=True
        )
 
        self.admin_project = Project.objects.create(
            name="Admin Project",
            organization=self.org,
            created_by=self.admin
        )
        
        self.member_project = Project.objects.create(
            name="Member Project",
            organization=self.org,
            created_by=self.member
        )
    
        self.task = Task.objects.create(
            project=self.admin_project,
            title="Test Task",
            created_by=self.admin,
            status="pending"
        )

    def get_token(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)


    
    def test_admin_can_create_project(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.get_token(self.admin)}")
        response = client.post("/api/projects/", {"name": "New Admin Project"})
        self.assertEqual(response.status_code, 201)

    def test_member_can_create_project(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.get_token(self.member)}")
        response = client.post("/api/projects/", {"name": "New Member Project"})
        self.assertEqual(response.status_code, 201)

    def test_viewer_cannot_create_project(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.get_token(self.viewer)}")
        response = client.post("/api/projects/", {"name": "New Viewer Project"})
        self.assertEqual(response.status_code, 403)

    def test_owner_can_create_project(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.get_token(self.owner)}")
        response = client.post("/api/projects/", {"name": "New Owner Project"})
        self.assertEqual(response.status_code, 201)


    def test_admin_can_view_all_projects(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.get_token(self.admin)}")
        response = client.get("/api/projects/")
        self.assertEqual(response.status_code, 200)
        # Admin should see all projects
        self.assertEqual(len(response.data["results"]), 2)

    def test_member_can_view_own_projects_only(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.get_token(self.member)}")
        response = client.get("/api/projects/")
        self.assertEqual(response.status_code, 200)
        # Member should only see projects they created
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Member Project")

    def test_viewer_can_view_all_projects_readonly(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.get_token(self.viewer)}")
        response = client.get("/api/projects/")
        self.assertEqual(response.status_code, 200)
        # Viewer should see all projects (read-only)
        self.assertEqual(len(response.data["results"]), 2)


    def test_admin_can_update_any_project(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.get_token(self.admin)}")
        response = client.patch(f"/api/projects/{self.member_project.id}/", 
                                {"name": "Updated By Admin"})
        self.assertEqual(response.status_code, 200)
        self.member_project.refresh_from_db()
        self.assertEqual(self.member_project.name, "Updated By Admin")

    def test_member_can_update_own_project(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.get_token(self.member)}")
        response = client.patch(f"/api/projects/{self.member_project.id}/", 
                                {"name": "Updated By Member"})
        self.assertEqual(response.status_code, 200)
        self.member_project.refresh_from_db()
        self.assertEqual(self.member_project.name, "Updated By Member")

    def test_member_cannot_update_admin_project(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.get_token(self.member)}")
        response = client.patch(f"/api/projects/{self.admin_project.id}/", 
                                {"name": "Hack Attempt"})
        self.assertEqual(response.status_code, 403)

    def test_viewer_cannot_update_any_project(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.get_token(self.viewer)}")
        response = client.patch(f"/api/projects/{self.admin_project.id}/", 
                                {"name": "Viewer Update"})
        self.assertEqual(response.status_code, 403)

    def test_admin_can_delete_any_project(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.get_token(self.admin)}")
        response = client.delete(f"/api/projects/{self.member_project.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Project.objects.filter(id=self.member_project.id).count(), 0)

    def test_member_can_delete_own_project(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.get_token(self.member)}")
        response = client.delete(f"/api/projects/{self.member_project.id}/")
        self.assertEqual(response.status_code, 204)

    def test_member_cannot_delete_admin_project(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.get_token(self.member)}")
        response = client.delete(f"/api/projects/{self.admin_project.id}/")
        self.assertEqual(response.status_code, 403)

    def test_viewer_cannot_delete_any_project(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.get_token(self.viewer)}")
        response = client.delete(f"/api/projects/{self.admin_project.id}/")
        self.assertEqual(response.status_code, 403)


    def test_member_can_create_task_in_own_project(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.get_token(self.member)}")
        response = client.post("/api/projects/tasks/", {
            "project": self.member_project.id,
            "title": "Member Task"
        })
        self.assertEqual(response.status_code, 201)

    def test_member_cannot_create_task_in_admin_project(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.get_token(self.member)}")
        response = client.post("/api/projects/tasks/", {
            "project": self.admin_project.id,
            "title": "Hack Task"
        })
        self.assertEqual(response.status_code, 404)

    def test_viewer_cannot_create_task(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.get_token(self.viewer)}")
        response = client.post("/api/projects/tasks/", {
            "project": self.admin_project.id,
            "title": "Viewer Task"
        })
        self.assertEqual(response.status_code, 403)

    def test_viewer_can_view_tasks(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.get_token(self.viewer)}")
        response = client.get(f"/api/projects/tasks/?project_id={self.admin_project.id}")
        self.assertEqual(response.status_code, 200)