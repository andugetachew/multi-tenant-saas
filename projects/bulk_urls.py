from django.urls import path
from .bulk_ops import BulkProjectDeleteView, BulkTaskUpdateView, BulkProjectArchiveView

urlpatterns = [
    path(
        "projects/delete/", BulkProjectDeleteView.as_view(), name="bulk-project-delete"
    ),
    path(
        "projects/archive/",
        BulkProjectArchiveView.as_view(),
        name="bulk-project-archive",
    ),
    path("tasks/update/", BulkTaskUpdateView.as_view(), name="bulk-task-update"),
]
