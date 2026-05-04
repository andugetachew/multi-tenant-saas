# scripts/backup_db.py
import os
import subprocess
from datetime import datetime
from django.conf import settings


def backup_database():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backups/saas_backup_{timestamp}.sql"

    os.makedirs("backups", exist_ok=True)

    # PostgreSQL backup
    subprocess.run(
        [
            "pg_dump",
            settings.DATABASES["default"]["NAME"],
            "-U",
            settings.DATABASES["default"]["USER"],
            "-h",
            settings.DATABASES["default"]["HOST"],
            "-p",
            settings.DATABASES["default"]["PORT"],
            "-f",
            backup_file,
        ]
    )

    # Compress backup
    subprocess.run(["gzip", backup_file])

    # Delete backups older than 30 days
    os.system('find backups -name "*.sql.gz" -mtime +30 -delete')

    print(f"Backup created: {backup_file}.gz")
    return backup_file


if __name__ == "__main__":
    backup_database()
