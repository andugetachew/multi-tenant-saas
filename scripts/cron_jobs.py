# scripts/cron_jobs.py
from datetime import datetime
import subprocess


def daily_maintenance():
    print(f"Running daily maintenance at {datetime.now()}")

    # Clean old sessions
    subprocess.run(["python", "manage.py", "clearsessions"])

    # Update search index
    subprocess.run(["python", "manage.py", "update_index"])

    # Send daily reports
    subprocess.run(["python", "manage.py", "send_daily_reports"])

    # Process recurring tasks
    from projects.recurring import process_recurring_tasks

    process_recurring_tasks()


if __name__ == "__main__":
    daily_maintenance()
