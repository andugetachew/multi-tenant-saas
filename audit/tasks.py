# audit/tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from audit.models import AuditLog


@shared_task
def cleanup_old_logs():
    """Delete audit logs older than 90 days"""
    cutoff_date = timezone.now() - timedelta(days=90)
    deleted_count = AuditLog.objects.filter(created_at__lt=cutoff_date).delete()
    return f"Deleted {deleted_count[0]} old audit logs"
