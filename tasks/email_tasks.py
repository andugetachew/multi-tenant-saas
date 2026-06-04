# tasks/email_tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def send_verification_email_task(user_email, verification_link):
    """Send email verification link"""
    try:
        send_mail(
            subject="Verify Your Email",
            message=f"Click here to verify your email: {verification_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        return f"Verification email sent to {user_email}"
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


@shared_task
def send_password_reset_email_task(user_email, reset_link):
    """Send password reset link"""
    try:
        send_mail(
            subject="Password Reset Request",
            message=f"Click here to reset your password: {reset_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        return f"Password reset email sent to {user_email}"
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


@shared_task
def send_welcome_email_task(user_email, organization_name):
    """Send welcome email after registration"""
    try:
        send_mail(
            subject=f"Welcome to {organization_name}!",
            message=f"Thank you for joining {organization_name}. Get started by creating your first project.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        return f"Welcome email sent to {user_email}"
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
