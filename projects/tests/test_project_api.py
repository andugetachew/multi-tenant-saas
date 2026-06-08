from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from organizations.models import Organization
from accounts.models import User
from projects.models import Project, Task


def make_client(user):
    refresh = RefreshToken.for_user(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return client


class ProjectAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Test Org", plan="basic")
        self.user = User.objects.create_user(
            email="projectapi_user@example.com",
            password="pass123",
            organization=self.org,
            is_email_verified=True,
            role="admin",
        )
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_create_project(self):
        url = reverse("project-list")
        data = {"name": "New Project", "description": "Test description"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "New Project")
        self.assertEqual(response.data["organization"], self.org.id)

    def test_list_projects(self):
        Project.objects.create(name="Test Project 1", organization=self.org, created_by=self.user)
        Project.objects.create(name="Test Project 2", organization=self.org, created_by=self.user)
        url = reverse("project-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        results = [p for p in response.data["results"] if p["organization"] == self.org.id]
        self.assertEqual(len(results), 2)

    def test_get_project_detail(self):
        project = Project.objects.create(name="Detail Project", organization=self.org, created_by=self.user)
        url = reverse("project-detail", kwargs={"pk": project.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Detail Project")

    def test_update_project(self):
        project = Project.objects.create(name="Original Name", organization=self.org, created_by=self.user)
        url = reverse("project-detail", kwargs={"pk": project.id})
        response = self.client.patch(url, {"name": "Updated Name"}, format="json")
        self.assertEqual(response.status_code, 200)
        project.refresh_from_db()
        self.assertEqual(project.name, "Updated Name")

    def test_delete_project(self):
        project = Project.objects.create(name="To Delete", organization=self.org, created_by=self.user)
        url = reverse("project-detail", kwargs={"pk": project.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Project.objects.filter(id=project.id).exists())

    def test_unauthenticated_cannot_list_projects(self):
        self.client.credentials()
        url = reverse("project-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_viewer_cannot_create_project(self):
        viewer = User.objects.create_user(
            email="viewer@example.com", password="pass123",
            organization=self.org, is_email_verified=True, role="viewer",
        )
        client = make_client(viewer)
        response = client.post(reverse("project-list"), {"name": "Viewer Project"}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_viewer_can_read_projects(self):
        Project.objects.create(name="Readable", organization=self.org, created_by=self.user)
        viewer = User.objects.create_user(
            email="viewer2@example.com", password="pass123",
            organization=self.org, is_email_verified=True, role="viewer",
        )
        client = make_client(viewer)
        response = client.get(reverse("project-list"))
        self.assertEqual(response.status_code, 200)

    def test_viewer_cannot_update_project(self):
        project = Project.objects.create(name="No Touch", organization=self.org, created_by=self.user)
        viewer = User.objects.create_user(
            email="viewer3@example.com", password="pass123",
            organization=self.org, is_email_verified=True, role="viewer",
        )
        client = make_client(viewer)
        response = client.patch(reverse("project-detail", kwargs={"pk": project.id}), {"name": "X"}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_member_can_only_see_own_projects(self):
        member = User.objects.create_user(
            email="member@example.com", password="pass123",
            organization=self.org, is_email_verified=True, role="member",
        )
        Project.objects.create(name="Member Project", organization=self.org, created_by=member)
        Project.objects.create(name="Admin Project", organization=self.org, created_by=self.user)
        client = make_client(member)
        response = client.get(reverse("project-list"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(all(p["created_by"] == member.id for p in response.data["results"]))

    def test_member_cannot_delete_others_project(self):
        member = User.objects.create_user(
            email="member2@example.com", password="pass123",
            organization=self.org, is_email_verified=True, role="member",
        )
        project = Project.objects.create(name="Admin Only", organization=self.org, created_by=self.user)
        client = make_client(member)
        response = client.delete(reverse("project-detail", kwargs={"pk": project.id}))
        self.assertEqual(response.status_code, 403)

    def test_bulk_delete_projects(self):
        p1 = Project.objects.create(name="Bulk1", organization=self.org, created_by=self.user)
        p2 = Project.objects.create(name="Bulk2", organization=self.org, created_by=self.user)
        url = reverse("bulk-project-delete")
        response = self.client.post(url, {"project_ids": [p1.id, p2.id]}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["deleted_count"], 2)

    def test_bulk_delete_requires_ids(self):
        url = reverse("bulk-project-delete")
        response = self.client.post(url, {"project_ids": []}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_bulk_archive_projects(self):
        p1 = Project.objects.create(name="Archive1", organization=self.org, created_by=self.user)
        p2 = Project.objects.create(name="Archive2", organization=self.org, created_by=self.user)
        url = reverse("bulk-project-archive")
        response = self.client.post(url, {"project_ids": [p1.id, p2.id]}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["archived_count"], 2)
        p1.refresh_from_db()
        self.assertEqual(p1.status, "archived")

    def test_project_search(self):
        Project.objects.create(name="Django Backend", organization=self.org, created_by=self.user)
        Project.objects.create(name="React Frontend", organization=self.org, created_by=self.user)
        url = reverse("project-search")
        response = self.client.get(url, {"q": "Django"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Django Backend")

    def test_project_search_requires_query(self):
        url = reverse("project-search")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_dashboard_stats_no_org(self):
        temp_org = Organization.objects.create(name="Temp Org For Stats", plan="basic")
        user = User.objects.create_user(
            email="noorg_stats@example.com",
            password="pass123",
            organization=temp_org,
            is_email_verified=True,
            role="admin",
        )
        User.objects.filter(pk=user.pk).update(organization=None)
        user.refresh_from_db()

        client = make_client(user)
        response = client.get(reverse("dashboard-stats"))

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["organization_name"])
        self.assertEqual(response.data["total_projects"], 0)
        self.assertEqual(response.data["total_tasks"], 0)


    def test_dashboard_stats_with_org(self):
        Project.objects.create(name="P1", organization=self.org, created_by=self.user)
        Task.objects.create(
            title="T1", project=Project.objects.first(),
            created_by=self.user, status="completed"
        )
        response = self.client.get(reverse("dashboard-stats"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("total_projects", response.data)
        self.assertIn("completed_tasks", response.data)


class TaskAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name="Task Org", plan="basic")
        self.user = User.objects.create_user(
            email="taskapi_user@example.com", password="pass123",
            organization=self.org, is_email_verified=True, role="admin",
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
        self.project = Project.objects.create(
            name="Task Project", organization=self.org, created_by=self.user
        )

    def test_create_task(self):
        url = reverse("task-list")
        data = {"title": "New Task", "project": self.project.id, "priority": "high"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["title"], "New Task")

    def test_list_tasks(self):
        Task.objects.create(title="Task 1", project=self.project, created_by=self.user)
        Task.objects.create(title="Task 2", project=self.project, created_by=self.user)
        response = self.client.get(reverse("task-list"))
        self.assertEqual(response.status_code, 200)

    def test_list_tasks_filtered_by_project(self):
        Task.objects.create(title="Task A", project=self.project, created_by=self.user)
        other_project = Project.objects.create(name="Other", organization=self.org, created_by=self.user)
        Task.objects.create(title="Task B", project=other_project, created_by=self.user)
        response = self.client.get(reverse("task-list"), {"project_id": self.project.id})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(all(t["project"] == self.project.id for t in response.data["results"]))

    def test_get_task_detail(self):
        task = Task.objects.create(title="Detail Task", project=self.project, created_by=self.user)
        response = self.client.get(reverse("task-detail", kwargs={"pk": task.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Detail Task")

    def test_update_task(self):
        task = Task.objects.create(title="Old Title", project=self.project, created_by=self.user)
        response = self.client.patch(
            reverse("task-detail", kwargs={"pk": task.id}),
            {"title": "New Title"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.title, "New Title")

    def test_delete_task(self):
        task = Task.objects.create(title="Delete Me", project=self.project, created_by=self.user)
        response = self.client.delete(reverse("task-detail", kwargs={"pk": task.id}))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Task.objects.filter(id=task.id).exists())

    def test_member_cannot_delete_unowned_task(self):
        member = User.objects.create_user(
            email="taskmember@example.com", password="pass123",
            organization=self.org, is_email_verified=True, role="member",
        )
        task = Task.objects.create(title="Admin Task", project=self.project, created_by=self.user)
        client = make_client(member)
        response = client.delete(reverse("task-detail", kwargs={"pk": task.id}))
        self.assertEqual(response.status_code, 403)

    def test_task_search(self):
        Task.objects.create(title="Fix login bug", project=self.project, created_by=self.user)
        Task.objects.create(title="Add dark mode", project=self.project, created_by=self.user)
        response = self.client.get(reverse("task-search"), {"q": "login"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_task_search_requires_query(self):
        response = self.client.get(reverse("task-search"))
        self.assertEqual(response.status_code, 400)

    def test_bulk_task_update(self):
        t1 = Task.objects.create(title="T1", project=self.project, created_by=self.user, status="pending")
        t2 = Task.objects.create(title="T2", project=self.project, created_by=self.user, status="pending")
        response = self.client.post(
            reverse("bulk-task-update"),
            {"task_ids": [t1.id, t2.id], "updates": {"status": "completed"}},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["updated_count"], 2)
        t1.refresh_from_db()
        self.assertEqual(t1.status, "completed")
        
    def test_bulk_task_update_requires_ids(self):
        response = self.client.post(
            reverse("bulk-task-update"),
            {"task_ids": [], "updates": {"status": "completed"}},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "No task IDs provided")