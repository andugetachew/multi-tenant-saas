from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def send_verification_email_task(user_email, verification_link):
    """Send email verification link"""
    try:
        send_mail(
            "Verify Your Email",
            f"Click here to verify: {verification_link}",
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


@shared_task
def send_password_reset_email_task(user_email, reset_link):
    """Send password reset link"""
    try:
        send_mail(
            "Password Reset Request",
            f"Click here to reset: {reset_link}",
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False
