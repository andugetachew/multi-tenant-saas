import pytest
from unittest.mock import patch
from django.core import mail

from organizations.models import Organization
from accounts.models import User
from notifications.email_utils import (
    send_email_notification,
    send_welcome_email,
    send_project_invitation_email,
)


@pytest.fixture
def org(db):
    return Organization.objects.create(name="Acme Corp")


@pytest.fixture
def user(org):
    return User.objects.create_user(
        email="u@acme.com", password="pass123", organization=org, first_name="Jane"
    )


@pytest.mark.django_db
class TestSendEmailNotification:
    def test_sends_plain_message_without_template(self, user):
        result = send_email_notification(user, "Hello", "World")

        assert result is True
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [user.email]
        assert mail.outbox[0].subject == "Hello"

    def test_returns_false_on_exception(self, user):
        with patch("notifications.email_utils.send_mail", side_effect=Exception("smtp down")):
            result = send_email_notification(user, "Hello", "World")
        assert result is False


@pytest.mark.django_db
class TestSendWelcomeEmail:
    def test_sends_welcome_email_with_org_name(self, user, org):
        result = send_welcome_email(user)

        assert result is True
        assert org.name in mail.outbox[0].subject


@pytest.mark.django_db
class TestSendProjectInvitationEmail:
    def test_sends_invitation_email(self, user, org):
        inviter = User.objects.create_user(
            email="inviter@acme.com", password="pass123", organization=org
        )
        result = send_project_invitation_email(user, inviter, org)

        assert result is True
        assert org.name in mail.outbox[0].subject