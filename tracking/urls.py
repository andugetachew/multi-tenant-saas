from django.urls import path
from .views import TimeEntryListCreateView, TimeEntryDetailView, TaskTimeSummaryView

urlpatterns = [
    path("", TimeEntryListCreateView.as_view(), name="time-entries"),
    path("<int:pk>/", TimeEntryDetailView.as_view(), name="time-entry-detail"),
    path(
        "task/<int:task_id>/", TaskTimeSummaryView.as_view(), name="task-time-summary"
    ),
]
