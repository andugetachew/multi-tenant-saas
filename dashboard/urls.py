from django.urls import path
from .views import RealTimeDashboardView

urlpatterns = [
    path("realtime/", RealTimeDashboardView.as_view(), name="realtime-dashboard"),
]
