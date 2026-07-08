
import pytest
from django.test import Client
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import User
from organizations.models import Organization
from projects.models import Project, Task

def pytest_configure(config):
    from django.conf import settings
    settings.TESTING = True
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True

def pytest_sessionstart(session):
    from django.conf import settings
    settings.REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []
    settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {}

@pytest.fixture
def api_client():
    """Return DRF API client"""
    return APIClient()


@pytest.fixture
def django_client():
    """Return Django test client"""
    return Client()


@pytest.fixture
def test_organization():
    """Create and return test organization"""
    org = Organization.objects.create(
        name="Test Organization", plan="basic", subscription_status="active"
    )
    return org


@pytest.fixture
def test_user(test_organization):
    """Create and return test user with organization"""
    user = User.objects.create_user(
        email="testuser@example.com",
        password="testpass123",
        organization=test_organization,
        is_email_verified=True,
        is_active=True,
        role="admin",
    )
    return user


@pytest.fixture
def test_owner(test_organization):
    """Create and return organization owner"""
    user = User.objects.create_user(
        email="owner@example.com",
        password="ownerpass123",
        organization=test_organization,
        is_email_verified=True,
        is_active=True,
        is_owner=True,
    )
    return user


@pytest.fixture
def test_member(test_organization):
    """Create and return organization member"""
    user = User.objects.create_user(
        email="member@example.com",
        password="memberpass123",
        organization=test_organization,
        is_email_verified=True,
        is_active=True,
        role="member",
    )
    return user


@pytest.fixture
def test_viewer(test_organization):
    """Create and return organization viewer"""
    user = User.objects.create_user(
        email="viewer@example.com",
        password="viewerpass123",
        organization=test_organization,
        is_email_verified=True,
        is_active=True,
        role="viewer",
    )
    return user


@pytest.fixture
def test_project(test_user, test_organization):
    """Create and return test project"""
    project = Project.objects.create(
        name="Test Project",
        description="Test Description",
        organization=test_organization,
        created_by=test_user,
        status="active",
    )
    return project


@pytest.fixture
def test_task(test_project, test_user):
    """Create and return test task"""
    task = Task.objects.create(
        project=test_project,
        title="Test Task",
        description="Task Description",
        status="pending",
        priority="medium",
        created_by=test_user,
    )
    return task


@pytest.fixture
def auth_client(test_user):
    """Return authenticated API client"""
    client = APIClient()
    refresh = RefreshToken.for_user(test_user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


@pytest.fixture
def owner_auth_client(test_owner):
    """Return authenticated owner client"""
    client = APIClient()
    refresh = RefreshToken.for_user(test_owner)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


@pytest.fixture
def member_auth_client(test_member):
    """Return authenticated member client"""
    client = APIClient()
    refresh = RefreshToken.for_user(test_member)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


@pytest.fixture
def valid_token(test_user):
    """Return valid JWT token"""
    refresh = RefreshToken.for_user(test_user)
    return str(refresh.access_token)



@pytest.fixture(autouse=True)
def disable_throttling(settings):
    settings.REST_FRAMEWORK = {
        **settings.REST_FRAMEWORK,
        'DEFAULT_THROTTLE_CLASSES': [],
        'DEFAULT_THROTTLE_RATES': {
            'user': '1000/day',
            'anon': '1000/day',
            'login': '1000/day',
            'register': '1000/day',
            'search': '1000/day',
        },
    }
    from accounts.views import RegisterView, LoginView, VerifyEmailView, PasswordResetRequestView
    RegisterView.throttle_classes = []
    LoginView.throttle_classes = []
    VerifyEmailView.throttle_classes = []
    PasswordResetRequestView.throttle_classes = []