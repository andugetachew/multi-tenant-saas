from django.urls import path
from .views import DashboardAnalyticsView
from django.urls import path
from .views import RevenueAnalyticsView, SellerPerformanceView, SystemHealthView

urlpatterns = [
    path("dashboard/", DashboardAnalyticsView.as_view(), name="analytics-dashboard"),
    path("revenue/", RevenueAnalyticsView.as_view(), name="revenue-analytics"),
    path("performance/", SellerPerformanceView.as_view(), name="seller-performance"),
    path("health/", SystemHealthView.as_view(), name="system-health"),
]
