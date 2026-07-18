import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from organizations.models import Organization
from accounts.models import User
from projects.models import Project
from custom_fields.models import CustomField, CustomFieldValue
from custom_fields.views import CustomFieldListCreateView, CustomFieldValueView

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
class TestCustomFieldListCreateView:
    def test_creates_field_scoped_to_organization(self, user, org):
        request = factory.post(
            "/api/custom-fields/",
            {"name": "Budget", "field_type": "number"},
            format="json",
        )
        force_authenticate(request, user=user)

        view = CustomFieldListCreateView.as_view()
        response = view(request)

        assert response.status_code == 201
        field = CustomField.objects.get(name="Budget")
        assert field.organization == org

    def test_only_lists_own_organization_fields(self, user, org):
        other_org = Organization.objects.create(name="Other")
        CustomField.objects.create(organization=org, name="Mine", field_type="text")
        CustomField.objects.create(organization=other_org, name="Not Mine", field_type="text")

        request = factory.get("/api/custom-fields/")
        force_authenticate(request, user=user)

        view = CustomFieldListCreateView.as_view()
        response = view(request)

        names = [f["name"] for f in response.data["results"]]
        assert "Mine" in names
        assert "Not Mine" not in names


@pytest.mark.django_db
class TestCustomFieldValueView:
    def test_get_returns_values_for_project(self, user, project, org):
        field = CustomField.objects.create(organization=org, name="Budget", field_type="number")
        CustomFieldValue.objects.create(project=project, field=field, value="5000")

        request = factory.get("/api/custom-field-values/")
        force_authenticate(request, user=user)

        view = CustomFieldValueView.as_view()
        response = view(request, project_id=project.id)

        assert response.status_code == 200
        assert len(response.data) == 1

    def test_post_creates_new_value(self, user, project, org):
        field = CustomField.objects.create(organization=org, name="Priority", field_type="text")

        request = factory.post(
            "/api/custom-field-values/",
            {"field_id": field.id, "value": "High"},
            format="json",
        )
        force_authenticate(request, user=user)

        view = CustomFieldValueView.as_view()
        response = view(request, project_id=project.id)

        assert response.status_code == 201
        assert CustomFieldValue.objects.get(project=project, field=field).value == "High"

    def test_post_updates_existing_value(self, user, project, org):
        field = CustomField.objects.create(organization=org, name="Priority", field_type="text")
        CustomFieldValue.objects.create(project=project, field=field, value="Low")

        request = factory.post(
            "/api/custom-field-values/",
            {"field_id": field.id, "value": "High"},
            format="json",
        )
        force_authenticate(request, user=user)

        view = CustomFieldValueView.as_view()
        response = view(request, project_id=project.id)

        assert response.status_code == 201
        assert CustomFieldValue.objects.filter(project=project, field=field).count() == 1
        assert CustomFieldValue.objects.get(project=project, field=field).value == "High"