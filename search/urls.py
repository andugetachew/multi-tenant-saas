from django.urls import path
from .views import GlobalSearchView

app_name = "search"

urlpatterns = [
    path("global/", GlobalSearchView.as_view(), name="global-search"),
]
