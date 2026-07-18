import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from organizations.models import Organization
from accounts.models import User
from projects.models import Project
from chat.models import ChatMessage
from chat.views import ChatMessageListCreateView

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


@pytest.mark.django_db
class TestChatMessageListCreateView:
    def test_creates_message_with_authenticated_user(self, user, project):
        request = factory.post(
            "/api/chat/", {"project": project.id, "message": "Hello team"}, format="json"
        )
        force_authenticate(request, user=user)

        view = ChatMessageListCreateView.as_view()
        response = view(request)

        assert response.status_code == 201
        msg = ChatMessage.objects.get(project=project)
        assert msg.user == user
        assert msg.message == "Hello team"

    def test_filters_by_project_id_query_param(self, user, project):
        other_project = Project.objects.create(organization=project.organization, name="P2", created_by=user)
        ChatMessage.objects.create(project=project, user=user, message="In P1")
        ChatMessage.objects.create(project=other_project, user=user, message="In P2")

        request = factory.get(f"/api/chat/?project_id={project.id}")
        force_authenticate(request, user=user)

        view = ChatMessageListCreateView.as_view()
        response = view(request)

        results = response.data["results"]
        assert len(results) == 1
        assert results[0]["message"] == "In P1"

    def test_only_lists_own_organization_messages(self, user, project):
        other_org = Organization.objects.create(name="Other")
        other_user = User.objects.create_user(
            email="other@test.com", password="pass123", organization=other_org
        )
        other_project = Project.objects.create(organization=other_org, name="OtherP", created_by=other_user)
        ChatMessage.objects.create(project=project, user=user, message="Mine")
        ChatMessage.objects.create(project=other_project, user=other_user, message="Not Mine")

        request = factory.get("/api/chat/")
        force_authenticate(request, user=user)

        view = ChatMessageListCreateView.as_view()
        response = view(request)

        messages = [m["message"] for m in response.data["results"]]
        assert "Mine" in messages
        assert "Not Mine" not in messages