import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from organizations.models import Organization
from accounts.models import User
from projects.models import Project, Task
from projects.attachements_views import TaskAttachmentUploadView, TaskAttachmentListView

factory = APIRequestFactory()


@pytest.fixture
def org(db):
    return Organization.objects.create(name="Acme Corp")


@pytest.fixture
def user(org):
    return User.objects.create_user(email="u@acme.com", password="pass123", organization=org)


@pytest.fixture
def project(org, user):
    return Project.objects.create(organization=org, name="P1", created_by=user)


@pytest.fixture
def task(project):
    return Task.objects.create(project=project, title="T1")


@pytest.mark.django_db
class TestDuplicateTaskAttachmentUploadView:
    def test_invalid_task_id_crashes_instead_of_404(self, user):
        """
        Documents a real bug: unlike the equivalent view in
        projects/views.py (which we already tested and confirmed
        handles Task.DoesNotExist with a clean 404), this duplicate
        implementation has no exception handling at all — an invalid
        task_id crashes with an unhandled Task.DoesNotExist instead
        of returning a proper 404 response.
        """
        request = factory.post("/upload/", {}, format="multipart")
        force_authenticate(request, user=user)

        view = TaskAttachmentUploadView.as_view()
        with pytest.raises(Task.DoesNotExist):
            view(request, task_id=99999)

    def test_no_file_returns_400(self, user, task):
        request = factory.post("/upload/", {}, format="multipart")
        force_authenticate(request, user=user)

        view = TaskAttachmentUploadView.as_view()
        response = view(request, task_id=task.id)

        assert response.status_code == 400


@pytest.mark.django_db
class TestDuplicateTaskAttachmentListView:
    def test_invalid_task_id_crashes_instead_of_404(self, user):
        request = factory.get("/attachments/")
        force_authenticate(request, user=user)

        view = TaskAttachmentListView.as_view()
        with pytest.raises(Task.DoesNotExist):
            view(request, task_id=99999)