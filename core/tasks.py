# core/tasks.py
from celery import shared_task
from django.conf import settings
import subprocess
import os
from datetime import datetime
import boto3
from botocore.exceptions import ClientError


@shared_task
def database_backup():
    """Create database backup and upload to S3"""

    # Create backup directory
    backup_dir = "/tmp/db_backups"
    os.makedirs(backup_dir, exist_ok=True)

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"multitenant_saas_backup_{timestamp}.sql")

    # Create PostgreSQL backup
    try:
        subprocess.run(
            [
                "pg_dump",
                "-h",
                settings.DATABASES["default"]["HOST"],
                "-U",
                settings.DATABASES["default"]["USER"],
                "-d",
                settings.DATABASES["default"]["NAME"],
                "-f",
                backup_file,
                "--no-owner",
                "--no-privileges",
            ],
            check=True,
            capture_output=True,
        )

        # Compress backup
        compressed_file = f"{backup_file}.gz"
        subprocess.run(["gzip", backup_file], check=True)

        # Upload to S3 (if configured)
        if hasattr(settings, "AWS_STORAGE_BUCKET_NAME"):
            upload_to_s3(
                compressed_file, f"backups/{os.path.basename(compressed_file)}"
            )

        # Delete old backups (keep last 30)
        cleanup_old_backups()

        return f"Backup created: {compressed_file}"

    except subprocess.CalledProcessError as e:
        error_msg = f"Backup failed: {e.stderr.decode()}"
        print(error_msg)
        return error_msg


def upload_to_s3(file_path, s3_key):
    """Upload backup file to S3"""
    import boto3

    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )

    try:
        s3.upload_file(file_path, settings.AWS_STORAGE_BUCKET_NAME, s3_key)
        os.remove(file_path)
    except ClientError as e:
        print(f"S3 upload failed: {e}")


def cleanup_old_backups():
    """Keep only last 30 backups"""
    backup_dir = "/tmp/db_backups"
    backups = sorted([f for f in os.listdir(backup_dir) if f.endswith(".gz")])

    while len(backups) > 30:
        oldest = backups.pop(0)
        os.remove(os.path.join(backup_dir, oldest))
