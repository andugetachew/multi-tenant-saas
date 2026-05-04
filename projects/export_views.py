from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .export import export_projects_csv, export_tasks_csv, export_projects_pdf
from .export import export_projects_excel, export_projects_json


class ExportProjectsCSV(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return export_projects_csv(request.user)


class ExportTasksCSV(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        project_id = request.query_params.get("project_id")
        return export_tasks_csv(request.user, project_id)


class ExportProjectsPDF(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return export_projects_pdf(request.user)


class ExportProjectsExcel(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return export_projects_excel(request.user)


class ExportProjectsJSON(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return export_projects_json(request.user)
