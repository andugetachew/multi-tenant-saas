import csv
import pandas as pd
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from .models import Project, Task
import pandas as pd
from django.http import HttpResponse


def export_projects_csv(user):
    """Export projects to CSV"""
    projects = Project.objects.filter(organization=user.organization)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="projects.csv"'

    writer = csv.writer(response)
    writer.writerow(["ID", "Name", "Description", "Status", "Created At", "Task Count"])

    for project in projects:
        writer.writerow(
            [
                project.id,
                project.name,
                project.description,
                getattr(project, "status", "active"),
                project.created_at,
                project.tasks.count(),
            ]
        )

    return response


def export_tasks_csv(user, project_id=None):
    """Export tasks to CSV"""
    tasks = Task.objects.filter(project__organization=user.organization)
    if project_id:
        tasks = tasks.filter(project_id=project_id)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="tasks.csv"'

    writer = csv.writer(response)
    writer.writerow(
        ["ID", "Title", "Status", "Priority", "Project", "Due Date", "Created At"]
    )

    for task in tasks:
        writer.writerow(
            [
                task.id,
                task.title,
                task.status,
                task.priority,
                task.project.name,
                task.due_date,
                task.created_at,
            ]
        )

    return response


def export_projects_pdf(user):
    """Export projects to PDF"""
    projects = Project.objects.filter(organization=user.organization)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="projects.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter)
    elements = []

    # Title
    styles = getSampleStyleSheet()
    title = Paragraph(f"Projects Report - {user.organization.name}", styles["Title"])
    elements.append(title)

    # Table data
    data = [["Name", "Description", "Tasks", "Created"]]
    for project in projects:
        data.append(
            [
                project.name,
                project.description[:50],
                str(project.tasks.count()),
                project.created_at.strftime("%Y-%m-%d"),
            ]
        )

    table = Table(data)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 14),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )

    elements.append(table)
    doc.build(elements)
    return response


def export_projects_excel(user):
    """Export projects to Excel"""
    projects = Project.objects.filter(organization=user.organization)

    data = []
    for project in projects:
        data.append(
            {
                "ID": project.id,
                "Name": project.name,
                "Description": project.description,
                "Status": getattr(project, "status", "active"),
                "Tasks": project.tasks.count(),
                "Created": project.created_at.strftime("%Y-%m-%d %H:%M"),
            }
        )

    df = pd.DataFrame(data)
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="projects.xlsx"'
    df.to_excel(response, index=False)
    return response


def export_projects_json(user):
    """Export projects to JSON"""
    from django.core.serializers import serialize
    import json

    projects = Project.objects.filter(organization=user.organization)
    data = json.loads(serialize("json", projects))

    response = HttpResponse(content_type="application/json")
    response["Content-Disposition"] = 'attachment; filename="projects.json"'
    response.write(json.dumps(data, indent=2))
    return response
