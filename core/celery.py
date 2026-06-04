# core/celery.py
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


app.conf.beat_schedule = {
    "send-daily-reports": {
        "task": "notifications.tasks.send_daily_reports",
        "schedule": crontab(hour=9, minute=0),
    },
    "check-subscription-expiry": {
        "task": "billing.tasks.check_subscription_expiry",
        "schedule": crontab(hour=0, minute=0),
    },
    "cleanup-old-logs": {
        "task": "audit.tasks.cleanup_old_logs",
        "schedule": crontab(day_of_week=0, hour=3, minute=0),
    },
    "generate-daily-backup": {
        "task": "core.tasks.database_backup",
        "schedule": crontab(hour=2, minute=0),
    },
}
