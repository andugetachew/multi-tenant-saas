import pytest
from rest_framework import status
from rest_framework.test import APIClient
from organizations.models import Organization
from accounts.models import User
from projects.models import Project, Task


# ─── FIXTURES ────────────────────────────────────────────

@pytest.fixture
def setup(db):
    org = Organization.objects.create(name="Org A")
    owner = User.objects.create_user(
        email="owner@a.com", password="pass123",
        organization=org, is_owner=True,
        is_email_verified=True, is_active=True,
    )
    member = User.objects.create_user(
        email="member@a.com", password="pass123",
        organization=org, role="member",
        is_email_verified=True, is_active=True,
    )
    viewer = User.objects.create_user(
        email="viewer@a.com", password="pass123",
        organization=org, role="viewer",
        is_email_verified=True, is_active=True,
    )
    other_org = Organization.objects.create(name="Org B")
    outsider = User.objects.create_user(
        email="outsider@b.com", password="pass123",
        organization=other_org, is_owner=True,
        is_email_verified=True, is_active=True,
    )
    project = Project.objects.create(
        name="Test Project", organization=org, created_by=owner
    )
    task = Task.objects.create(
        title="Test Task", project=project, created_by=owner
    )
    return {
        "org": org, "owner": owner, "member": member,
        "viewer": viewer, "outsider": outsider,
        "project": project, "task": task,
    }


# ─── PROJECT LIST & CREATE ────────────────────────────────

class TestProjectListCreate:

    def test_unauthenticated_blocked(self, setup):
        r = APIClient().get("/api/projects/")
        assert r.status_code == status.HTTP_401_UNAUTHORIZED

    def test_member_sees_only_own_projects(self, setup):
        # member has no projects yet — list should be empty
        client = APIClient()
        client.force_authenticate(user=setup["member"])
        r = client.get("/api/projects/")
        assert r.status_code == status.HTTP_200_OK
        results = r.data.get("results", r.data)
        assert all(p["created_by"] == setup["member"].id for p in results)

    def test_outsider_cannot_see_org_projects(self, setup):
        client = APIClient()
        client.force_authenticate(user=setup["outsider"])
        r = client.get("/api/projects/")
        results = r.data.get("results", r.data)
        names = [p["name"] for p in results]
        assert "Test Project" not in names

    def test_create_project_missing_name(self, setup):
        client = APIClient()
        client.force_authenticate(user=setup["owner"])
        r = client.post("/api/projects/", {}, format="json")
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_project_unauthenticated(self, setup):
        r = APIClient().post("/api/projects/", {"name": "Ghost"}, format="json")
        assert r.status_code == status.HTTP_401_UNAUTHORIZED


# ─── PROJECT DETAIL ───────────────────────────────────────

class TestProjectDetail:

    def test_owner_can_retrieve(self, setup):
        client = APIClient()
        client.force_authenticate(user=setup["owner"])
        r = client.get(f"/api/projects/{setup['project'].pk}/")
        assert r.status_code == status.HTTP_200_OK

    def test_invalid_id_returns_404(self, setup):
        client = APIClient()
        client.force_authenticate(user=setup["owner"])
        r = client.get("/api/projects/99999/")
        assert r.status_code == status.HTTP_404_NOT_FOUND

    def test_outsider_cannot_retrieve(self, setup):
        client = APIClient()
        client.force_authenticate(user=setup["outsider"])
        r = client.get(f"/api/projects/{setup['project'].pk}/")
        assert r.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

    def test_viewer_cannot_update(self, setup):
        client = APIClient()
        client.force_authenticate(user=setup["viewer"])
        r = client.patch(
            f"/api/projects/{setup['project'].pk}/",
            {"name": "Hacked"}, format="json"
        )
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_member_cannot_delete_others_project(self, setup):
        client = APIClient()
        client.force_authenticate(user=setup["member"])
        r = client.delete(f"/api/projects/{setup['project'].pk}/")
        assert r.status_code == status.HTTP_403_FORBIDDEN

    def test_owner_can_delete_own_project(self, setup):
        client = APIClient()
        client.force_authenticate(user=setup["owner"])
        r = client.delete(f"/api/projects/{setup['project'].pk}/")
        assert r.status_code == status.HTTP_204_NO_CONTENT


# ─── TASK LIST & CREATE ───────────────────────────────────

class TestTaskListCreate:

    def test_unauthenticated_blocked(self, setup):
        r = APIClient().get("/api/projects/tasks/")
        assert r.status_code == status.HTTP_401_UNAUTHORIZED

    def test_task_create_invalid_project_id(self, setup):
        client = APIClient()
        client.force_authenticate(user=setup["owner"])
        r = client.post("/api/projects/tasks/", {
            "title": "Task", "project": 99999
        }, format="json")
        assert r.status_code == status.HTTP_404_NOT_FOUND

    def test_task_create_missing_title(self, setup):
        client = APIClient()
        client.force_authenticate(user=setup["owner"])
        r = client.post("/api/projects/tasks/", {
            "project": setup["project"].pk
        }, format="json")
        assert r.status_code == status.HTTP_400_BAD_REQUEST

    def test_member_cannot_create_task_on_others_project(self, setup):
        client = APIClient()
        client.force_authenticate(user=setup["member"])
        r = client.post("/api/projects/tasks/", {
            "title": "Sneaky Task",
            "project": setup["project"].pk  # owned by owner, not member
        }, format="json")
        assert r.status_code in [
            status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND
        ]

    def test_filter_tasks_by_project_id(self, setup):
        client = APIClient()
        client.force_authenticate(user=setup["owner"])
        r = client.get(f"/api/projects/tasks/?project_id={setup['project'].pk}")
        assert r.status_code == status.HTTP_200_OK
        results = r.data.get("results", r.data)
        assert all(t["project"] == setup["project"].pk for t in results)


# ─── TASK DETAIL ─────────────────────────────────────────

class TestTaskDetail:

    def test_invalid_task_id_returns_404(self, setup):
        client = APIClient()
        client.force_authenticate(user=setup["owner"])
        r = client.get("/api/projects/tasks/99999/")
        assert r.status_code == status.HTTP_404_NOT_FOUND

    def test_outsider_cannot_access_task(self, setup):
        client = APIClient()
        client.force_authenticate(user=setup["outsider"])
        r = client.get(f"/api/projects/tasks/{setup['task'].pk}/")
        assert r.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

    def test_member_cannot_delete_unrelated_task(self, setup):
        client = APIClient()
        client.force_authenticate(user=setup["member"])
        r = client.delete(f"/api/projects/tasks/{setup['task'].pk}/")
        assert r.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

    def test_owner_can_delete_task(self, setup):
        client = APIClient()
        client.force_authenticate(user=setup["owner"])
        r = client.delete(f"/api/projects/tasks/{setup['task'].pk}/")
        assert r.status_code == status.HTTP_204_NO_CONTENT


# ─── DASHBOARD STATS ─────────────────────────────────────

class TestDashboardStats:

    def test_unauthenticated_blocked(self, setup):
        r = APIClient().get("/api/projects/dashboard/stats/")
        assert r.status_code == status.HTTP_401_UNAUTHORIZED

    def test_owner_gets_full_stats(self, setup):
        client = APIClient()
        client.force_authenticate(user=setup["owner"])
        r = client.get("/api/projects/dashboard/stats/")
        assert r.status_code == status.HTTP_200_OK
        assert "total_projects" in r.data
        assert "total_tasks" in r.data

    def test_member_stats_scoped_to_own_data(self, setup):
        client = APIClient()
        client.force_authenticate(user=setup["member"])
        r = client.get("/api/projects/dashboard/stats/")
        assert r.status_code == status.HTTP_200_OK
        # member has no projects, so total should be 0
        assert r.data["total_projects"] == 0