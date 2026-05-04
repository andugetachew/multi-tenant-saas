from datetime import timedelta
from django.utils import timezone
from .models import RecurringTask, Task


def process_recurring_tasks():
    now = timezone.now()
    recurring_tasks = RecurringTask.objects.filter(
        is_active=True, next_due_date__lte=now
    )

    for rt in recurring_tasks:
        # Create new task
        Task.objects.create(
            project=rt.project,
            title=rt.title,
            description=rt.description,
            priority=rt.priority,
            status="pending",
        )

        # Update next due date
        if rt.frequency == "daily":
            rt.next_due_date += timedelta(days=1)
        elif rt.frequency == "weekly":
            rt.next_due_date += timedelta(weeks=1)
        elif rt.frequency == "monthly":
            rt.next_due_date += timedelta(days=30)
        elif rt.frequency == "quarterly":
            rt.next_due_date += timedelta(days=90)

        rt.save()
