# scripts/backup.py
import subprocess
import os
from datetime import datetime


def backup_database():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backups/db_backup_{timestamp}.sql"

    os.makedirs("backups", exist_ok=True)

    subprocess.run(
        [
            "pg_dump",
            "-U",
            "postgres",
            "-d",
            "multi_tenant_saas",
            "-f",
            backup_file,
        ]
    )

    print(f"✅ Backup created: {backup_file}")


if __name__ == "__main__":
    backup_database()
