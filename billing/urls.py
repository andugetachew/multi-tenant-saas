from django.urls import path
from .views import (
    PlanListView,
    CurrentSubscriptionView,
    RequestUpgradeView,
    AdminApproveUpgradeView,
)

urlpatterns = [
    path("plans/", PlanListView.as_view(), name="plans"),
    path("subscription/", CurrentSubscriptionView.as_view(), name="subscription"),
    path("upgrade/request/", RequestUpgradeView.as_view(), name="request-upgrade"),
    path(
        "admin/approve/<int:invoice_id>/",
        AdminApproveUpgradeView.as_view(),
        name="admin-approve",
    ),
]
