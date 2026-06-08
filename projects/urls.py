from django.urls import path
from .views import (
    ProjectListCreateView,
    ProjectDetailView,
    TaskListCreateView,
    TaskDetailView,
    DashboardStatsView,
    ProjectSearchView,
    TaskSearchView,
    BulkProjectDeleteView,
    BulkTaskUpdateView,
    BulkProjectArchiveView,
)
from .export_views import ExportProjectsCSV, ExportTasksCSV, ExportProjectsPDF

urlpatterns = [
    path("", ProjectListCreateView.as_view(), name="project-list"),
    path("<int:pk>/", ProjectDetailView.as_view(), name="project-detail"),
    path("tasks/", TaskListCreateView.as_view(), name="task-list"),
    path("tasks/<int:pk>/", TaskDetailView.as_view(), name="task-detail"),
    path("dashboard/stats/", DashboardStatsView.as_view(), name="dashboard-stats"),
    path("search/", ProjectSearchView.as_view(), name="project-search"),
    path("tasks/search/", TaskSearchView.as_view(), name="task-search"),
    path("bulk-delete/", BulkProjectDeleteView.as_view(), name="bulk-project-delete"),
    path("bulk-archive/", BulkProjectArchiveView.as_view(), name="bulk-project-archive"),
    path("tasks/bulk-update/", BulkTaskUpdateView.as_view(), name="bulk-task-update"),
    path("export/projects/csv/", ExportProjectsCSV.as_view(), name="export-projects-csv"),
    path("export/tasks/csv/", ExportTasksCSV.as_view(), name="export-tasks-csv"),
    path("export/projects/pdf/", ExportProjectsPDF.as_view(), name="export-projects-pdf"),
]