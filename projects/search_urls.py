from django.urls import path
from .views import ProjectSearchView, TaskSearchView

urlpatterns = [
    path("projects/", ProjectSearchView.as_view(), name="search-projects"),
    path("tasks/", TaskSearchView.as_view(), name="search-tasks"),
]
