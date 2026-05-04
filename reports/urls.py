from django.urls import path
from .views import AdvancedReportView

urlpatterns = [
    path("advanced/", AdvancedReportView.as_view(), name="advanced-report"),
]
