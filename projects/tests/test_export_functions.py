import csv
import io
import json
import pytest

from organizations.models import Organization
from accounts.models import User
from projects.models import Project, Task
from projects.export import (
    export_projects_csv,
    export_tasks_csv,
    export_projects_pdf,
    export_projects_excel,
    export_projects_json,
)


@pytest.fixture
def org(db):
    return Organization.objects.create(name="Acme Corp")


@pytest.fixture
def user(org):
    return User.objects.create_user(email="u@acme.com", password="pass123", organization=org)


@pytest.fixture
def project(org, user):
    return Project.objects.create(organization=org, name="P1", description="desc", created_by=user)


@pytest.mark.django_db
class TestExportProjectsCsv:
    def test_returns_csv_with_project_row(self, user, project):
        response = export_projects_csv(user)

        assert response["Content-Type"] == "text/csv"
        content = response.content.decode()
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)

        assert rows[0] == ["ID", "Name", "Description", "Status", "Created At", "Task Count"]
        assert rows[1][1] == "P1"

    def test_only_includes_own_organization_projects(self, user):
        other_org = Organization.objects.create(name="Other Corp")
        Project.objects.create(organization=other_org, name="Not Mine")

        response = export_projects_csv(user)
        content = response.content.decode()
        assert "Not Mine" not in content


@pytest.mark.django_db
class TestExportTasksCsv:
    def test_returns_csv_with_task_row(self, user, project):
        Task.objects.create(project=project, title="T1", status="pending", priority="high")

        response = export_tasks_csv(user)
        content = response.content.decode()
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)

        assert rows[0] == ["ID", "Title", "Status", "Priority", "Project", "Due Date", "Created At"]
        assert rows[1][1] == "T1"

    def test_filters_by_project_id(self, user, project):
        other_project = Project.objects.create(
            organization=project.organization, name="P2", created_by=user
        )
        Task.objects.create(project=project, title="Mine")
        Task.objects.create(project=other_project, title="Other")

        response = export_tasks_csv(user, project_id=project.id)
        content = response.content.decode()

        assert "Mine" in content
        assert "Other" not in content


@pytest.mark.django_db
class TestExportProjectsPdf:
    def test_returns_pdf_response(self, user, project):
        response = export_projects_pdf(user)

        assert response["Content-Type"] == "application/pdf"
        assert len(response.content) > 0

    def test_handles_empty_description_gracefully(self, user, org):
        Project.objects.create(organization=org, name="NoDesc", description="", created_by=user)
        response = export_projects_pdf(user)
        assert response.status_code == 200


@pytest.mark.django_db
class TestExportProjectsExcel:
    def test_returns_xlsx_response(self, user, project):
        response = export_projects_excel(user)

        assert response["Content-Type"] == (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        assert len(response.content) > 0


@pytest.mark.django_db
class TestExportProjectsJson:
    def test_returns_json_with_project_data(self, user, project):
        response = export_projects_json(user)

        assert response["Content-Type"] == "application/json"
        data = json.loads(response.content)
        assert len(data) == 1
        assert data[0]["fields"]["name"] == "P1"