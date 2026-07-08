from django.urls import path
from .views import (
    PlanListView,
    CurrentSubscriptionView,
    RequestUpgradeView,
    AdminApproveUpgradeView,
)
from .views import (
    PlanListView,
    CurrentSubscriptionView,
    RequestUpgradeView,
    AdminApproveUpgradeView,
    CreateCheckoutSessionView,
    StripeWebhookView,
    CancelSubscriptionView,
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
    path("cancel/", CancelSubscriptionView.as_view(), name="cancel-subscription"),
    path("plans/", PlanListView.as_view(), name="plans"),
    path("subscription/", CurrentSubscriptionView.as_view(), name="subscription"),
    path("upgrade/request/", RequestUpgradeView.as_view(), name="request-upgrade"),
    path("admin/approve/<int:invoice_id>/", AdminApproveUpgradeView.as_view(), name="admin-approve"),
    path("checkout/", CreateCheckoutSessionView.as_view(), name="create-checkout"),
    path("webhook/stripe/", StripeWebhookView.as_view(), name="stripe-webhook"),
]

