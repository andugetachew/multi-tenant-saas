from django.urls import path
from .views import AdvancedReportView, ComprehensiveReportView

urlpatterns = [
    path("advanced/", AdvancedReportView.as_view(), name="advanced-report"),
    path(
        "comprehensive/", ComprehensiveReportView.as_view(), name="comprehensive-report"
    ),
]
