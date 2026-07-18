import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from organizations.models import Organization
from accounts.models import User
from projects.models import Project, Task
from projects.task_comments import TaskCommentView

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
class TestTaskCommentView:
    def test_creating_comment_crashes_because_comment_model_has_no_task_field(
        self, user, task, project
    ):
        """
        Documents a real bug: TaskCommentView.perform_create() calls
        serializer.save(..., task=task), but the Comment model has no
        `task` field — only project, user, parent, content. Passing
        project explicitly (required since it's not read_only on the
        serializer) gets validation past the 400 stage, exposing the
        real crash when Comment.objects.create() receives an
        unrecognized `task` keyword argument.
        """
        request = factory.post(
            f"/api/tasks/{task.id}/comments/",
            {"content": "hello", "project": project.id},
            format="json",
        )
        force_authenticate(request, user=user)

        view = TaskCommentView.as_view()
        with pytest.raises(TypeError):
            view(request, task_id=task.id)