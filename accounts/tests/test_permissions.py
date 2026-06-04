# from django.test import TestCase
# from rest_framework.test import APIClient
# from rest_framework_simplejwt.tokens import RefreshToken
# from accounts.models import User
# from organizations.models import Organization


# class RoleBasedPermissionsTestCase(TestCase):
#     """Test RBAC + Tenant Isolation for SaaS"""

#     def setUp(self):
#         self.org = Organization.objects.create(name="Test Org")
#         self.other_org = Organization.objects.create(name="Other Org")

#         self.admin_user = self._create_user("admin@example.com", "admin", False, "admin")
#         self.member_user = self._create_user("member@example.com", "member", False, "member")
#         self.viewer_user = self._create_user("viewer@example.com", "viewer", False, "viewer")
#         self.owner_user = self._create_user("owner@example.com", "owner", True, "member")
#         self.other_org_user = self._create_user("other@example.com", "other", False, "member", self.other_org)

  
#     def _create_user(self, email, password, is_owner, role, org=None):
#         return User.objects.create_user(
#             email=email,
#             password="pass123",
#             organization=org or self.org,
#             role=role,
#             is_owner=is_owner,
#         )

#     def _client(self, user):
#         refresh = RefreshToken.for_user(user)
#         client = APIClient()
#         client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
#         return client

  

#     def test_admin_can_create_project(self):
#         client = self._client(self.admin_user)

#         response = client.post("/api/projects/", {"name": "Admin Project"})
#         self.assertEqual(response.status_code, 201)

#     def test_member_can_create_project(self):
#         client = self._client(self.member_user)

#         response = client.post("/api/projects/", {"name": "Member Project"})
#         self.assertEqual(response.status_code, 201)

#     def test_viewer_cannot_create_project(self):
#         client = self._client(self.viewer_user)

#         response = client.post("/api/projects/", {"name": "Viewer Project"})
#         self.assertEqual(response.status_code, 403)

   

#     def test_other_org_cannot_access_projects(self):
#         client = self._client(self.other_org_user)

#         response = client.get("/api/projects/")

#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(len(response.data.get("results", [])), 0)


#     def test_viewer_cannot_update_project(self):
#         client = self._client(self.viewer_user)

#         response = client.patch("/api/projects/1/", {"name": "Hacked"})
#         self.assertIn(response.status_code, [403, 404])

   

#     def test_member_can_delete_project_or_forbidden(self):
#         client = self._client(self.member_user)

#         response = client.delete("/api/projects/1/")

#         self.assertIn(response.status_code, [204, 403])

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import User
from organizations.models import Organization
from projects.models import Project
import uuid


class RoleBasedPermissionsTestCase(TestCase):
    """Test RBAC + Tenant Isolation for SaaS"""

    def setUp(self):
        self.org = Organization.objects.create(name="Test Org")
        self.other_org = Organization.objects.create(name="Other Org")

        # Use unique emails to avoid duplicates
        self.admin_user = self._create_user(f"admin_{uuid.uuid4()}@example.com", "admin", False, "admin")
        self.member_user = self._create_user(f"member_{uuid.uuid4()}@example.com", "member", False, "member")
        self.viewer_user = self._create_user(f"viewer_{uuid.uuid4()}@example.com", "viewer", False, "viewer")
        self.owner_user = self._create_user(f"owner_{uuid.uuid4()}@example.com", "owner", True, "member")
        self.other_org_user = self._create_user(f"other_{uuid.uuid4()}@example.com", "other", False, "member", self.other_org)

        # Create test projects
        self.admin_project = Project.objects.create(
            name="Admin Project",
            organization=self.org,
            created_by=self.admin_user
        )
        self.member_project = Project.objects.create(
            name="Member Project",
            organization=self.org,
            created_by=self.member_user
        )

    def _create_user(self, email, password, is_owner, role, org=None):
        return User.objects.create_user(
            email=email,
            password="pass123",
            organization=org or self.org,
            role=role,
            is_owner=is_owner,
        )

    def _client(self, user):
        refresh = RefreshToken.for_user(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        return client

    def test_admin_can_create_project(self):
        client = self._client(self.admin_user)
        response = client.post("/api/projects/", {"name": "Admin Project"})
        self.assertEqual(response.status_code, 201)

    def test_member_can_create_project(self):
        client = self._client(self.member_user)
        response = client.post("/api/projects/", {"name": "Member Project"})
        self.assertEqual(response.status_code, 201)

    def test_viewer_cannot_create_project(self):
        client = self._client(self.viewer_user)
        response = client.post("/api/projects/", {"name": "Viewer Project"})
        self.assertEqual(response.status_code, 403)

    def test_other_org_cannot_access_projects(self):
        client = self._client(self.other_org_user)
        response = client.get("/api/projects/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data.get("results", [])), 0)

    def test_viewer_cannot_update_project(self):
        client = self._client(self.viewer_user)
        response = client.patch(f"/api/projects/{self.admin_project.id}/", {"name": "Hacked"})
        self.assertIn(response.status_code, [403, 404])

    def test_member_can_delete_own_project(self):
        client = self._client(self.member_user)
        response = client.delete(f"/api/projects/{self.member_project.id}/")
        self.assertEqual(response.status_code, 204)

    def test_member_cannot_delete_admin_project(self):
        client = self._client(self.member_user)
        response = client.delete(f"/api/projects/{self.admin_project.id}/")
        self.assertEqual(response.status_code, 403)