from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_email_notification(user, subject, message, email_template=None):
    """Send email notification to user"""
    try:
        if email_template:
            html_message = render_to_string(
                email_template, {"user": user, "subject": subject, "message": message}
            )
            plain_message = strip_tags(html_message)
        else:
            plain_message = message
            html_message = f"<h3>{subject}</h3><p>{message}</p>"

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
            html_message=html_message,
        )
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


def send_welcome_email(user):
    """Send welcome email to new user"""
    subject = f"Welcome to {user.organization.name}!"
    message = f"""
    Welcome {user.first_name or user.email}!
    
    You've been added to {user.organization.name} as a {user.role}.
    
    Login here: http://localhost:8000/admin
    Email: {user.email}
    
    Get started by creating your first project!
    """
    return send_email_notification(user, subject, message)


def send_project_invitation_email(user, invited_by, organization):
    """Send project invitation email"""
    subject = f"You've been invited to join {organization.name}"
    message = f"""
    {invited_by.email} has invited you to join {organization.name}.
    
    Login to accept: http://localhost:8000/api/organizations/invite/
    
    Welcome aboard!
    """
    return send_email_notification(user, subject, message)
