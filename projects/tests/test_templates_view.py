import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from organizations.models import Organization
from accounts.models import User
from projects.templates import ProjectTemplateView

factory = APIRequestFactory()


@pytest.fixture
def org(db):
    return Organization.objects.create(name="Acme Corp")


@pytest.fixture
def user(org):
    return User.objects.create_user(email="u@acme.com", password="pass123", organization=org)


@pytest.mark.django_db
class TestProjectTemplateViewGet:
    def test_returns_all_three_templates(self, user):
        request = factory.get("/api/templates/")
        force_authenticate(request, user=user)
        response = ProjectTemplateView.as_view()(request)

        assert response.status_code == 200
        assert set(response.data.keys()) == {
            "software_development", "marketing_campaign", "event_planning"
        }
        assert len(response.data["software_development"]["tasks"]) == 6


@pytest.mark.django_db
class TestProjectTemplateViewPost:
    def test_unknown_template_returns_400(self, user):
        request = factory.post(
            "/api/templates/", {"template_name": "not_real"}, format="json"
        )
        force_authenticate(request, user=user)
        response = ProjectTemplateView.as_view()(request)

        assert response.status_code == 400

    def test_creating_project_from_known_template_crashes(self, user):
        """
        Documents a severe real bug: the templates dict inside post()
        uses literal `{...}` (Python's Ellipsis) as placeholder values
        instead of the actual template data used in get(). Any valid
        template_name passes the 'not found' check but then crashes
        with TypeError when the code tries to subscript Ellipsis
        (template["description"]). Every POST request to this endpoint
        currently fails for every template.
        """
        request = factory.post(
            "/api/templates/",
            {"template_name": "software_development", "name": "My New Project"},
            format="json",
        )
        force_authenticate(request, user=user)

        with pytest.raises(TypeError):
            ProjectTemplateView.as_view()(request)