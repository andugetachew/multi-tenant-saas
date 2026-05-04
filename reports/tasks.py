from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from projects.export import export_projects_csv
from accounts.models import User


@shared_task
def send_daily_report(organization_id):
    from organizations.models import Organization

    org = Organization.objects.get(id=organization_id)

    # Generate report
    csv_data = export_projects_csv(org.users.first())

    # Send to all admins
    admins = org.users.filter(role="admin")
    for admin in admins:
        send_mail(
            f"Daily Report - {org.name}",
            "Your daily project report is attached.",
            "noreply@yourdomain.com",
            [admin.email],
            fail_silently=False,
            attachments=[("projects.csv", csv_data.content, "text/csv")],
        )


@shared_task
def send_weekly_summary():
    from organizations.models import Organization

    for org in Organization.objects.all():
        send_daily_report.delay(org.id)
