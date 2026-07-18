import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIRequestFactory, force_authenticate

from organizations.models import Organization
from accounts.models import User
from projects.models import Project, Task, TaskAttachment, TaskTemplate, RecurringTask
from projects.views import (
    ProjectListCreateView,
    TaskAttachmentUploadView,
    TaskAttachmentListView,
    TaskTemplateListCreateView,
    TaskTemplateDetailView,
    BulkProjectDeleteView,
)

factory = APIRequestFactory()


@pytest.fixture
def org(db):
    return Organization.objects.create(name="Acme Corp")


@pytest.fixture
def owner(org):
    return User.objects.create_user(
        email="owner@acme.com", password="pass123", organization=org, is_owner=True
    )


@pytest.fixture
def project(org, owner):
    return Project.objects.create(organization=org, name="P1", created_by=owner)


@pytest.fixture
def task(project):
    return Task.objects.create(project=project, title="T1")


@pytest.mark.django_db
class TestProjectAutoCreateOrganization:
    def test_project_creation_auto_creates_org_when_user_has_none(self):
        user = User.objects.create(email="noorg@test.com")
        user.set_password("pass123")
        user.organization = None
        user.save()

        request = factory.post("/api/projects/", {"name": "First Project"}, format="json")
        force_authenticate(request, user=user)

        view = ProjectListCreateView.as_view()
        response = view(request)

        user.refresh_from_db()
        assert response.status_code == 201
        assert user.organization is not None
        assert user.is_owner is True


@pytest.mark.django_db
class TestTaskAttachmentUploadView:
    def test_upload_success(self, owner, task):
        file = SimpleUploadedFile("doc.txt", b"file content", content_type="text/plain")
        request = factory.post("/upload/", {"file": file}, format="multipart")
        force_authenticate(request, user=owner)

        view = TaskAttachmentUploadView.as_view()
        response = view(request, task_id=task.id)

        assert response.status_code == 201
        assert response.data["filename"] == "doc.txt"
        assert TaskAttachment.objects.filter(task=task).count() == 1

    def test_upload_task_not_found(self, owner):
        request = factory.post("/upload/", {}, format="multipart")
        force_authenticate(request, user=owner)

        view = TaskAttachmentUploadView.as_view()
        response = view(request, task_id=99999)

        assert response.status_code == 404

    def test_upload_no_file_provided(self, owner, task):
        request = factory.post("/upload/", {}, format="multipart")
        force_authenticate(request, user=owner)

        view = TaskAttachmentUploadView.as_view()
        response = view(request, task_id=task.id)

        assert response.status_code == 400


@pytest.mark.django_db
class TestTaskAttachmentListView:
    def test_list_attachments(self, owner, task):
        TaskAttachment.objects.create(
            task=task, file=SimpleUploadedFile("a.txt", b"data"),
            filename="a.txt", file_size=4, uploaded_by=owner,
        )

        request = factory.get("/attachments/")
        force_authenticate(request, user=owner)

        view = TaskAttachmentListView.as_view()
        response = view(request, task_id=task.id)

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["filename"] == "a.txt"

    def test_list_task_not_found(self, owner):
        request = factory.get("/attachments/")
        force_authenticate(request, user=owner)

        view = TaskAttachmentListView.as_view()
        response = view(request, task_id=99999)

        assert response.status_code == 404


@pytest.mark.django_db
class TestBulkProjectDeleteView:
    def test_deletes_projects_in_organization(self, owner, org):
        p1 = Project.objects.create(organization=org, name="P1", created_by=owner)
        p2 = Project.objects.create(organization=org, name="P2", created_by=owner)

        request = factory.post(
            "/bulk-delete/", {"project_ids": [p1.id, p2.id]}, format="json"
        )
        force_authenticate(request, user=owner)

        view = BulkProjectDeleteView.as_view()
        response = view(request)

        assert response.status_code == 200
        assert response.data["deleted_count"] == 2
        assert Project.objects.filter(organization=org).count() == 0

    def test_empty_ids_returns_400(self, owner):
        request = factory.post("/bulk-delete/", {"project_ids": []}, format="json")
        force_authenticate(request, user=owner)

        view = BulkProjectDeleteView.as_view()
        response = view(request)

        assert response.status_code == 400


@pytest.mark.django_db
class TestTaskTemplateViews:
    def test_list_create_view_works(self, owner, org):
        request = factory.get("/templates/")
        force_authenticate(request, user=owner)

        view = TaskTemplateListCreateView.as_view()
        response = view(request)

        assert response.status_code == 200

    def test_can_create_template(self, owner, org):
        request = factory.post(
            "/templates/",
            {"name": "Standard Task", "priority": "medium"},
            format="json",
        )
        force_authenticate(request, user=owner)

        view = TaskTemplateListCreateView.as_view()
        response = view(request)

        assert response.status_code == 201
        assert TaskTemplate.objects.filter(organization=org, name="Standard Task").exists()

    def test_detail_view_works(self, owner, org):
        template = TaskTemplate.objects.create(organization=org, name="Standard Task")
        request = factory.get(f"/templates/{template.id}/")
        force_authenticate(request, user=owner)

        view = TaskTemplateDetailView.as_view()
        response = view(request, pk=template.id)

        assert response.status_code == 200
        assert response.data["name"] == "Standard Task"