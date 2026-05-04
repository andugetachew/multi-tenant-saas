from django.urls import path
from .views import WebhookListCreateView, WebhookDetailView

urlpatterns = [
    path("", WebhookListCreateView.as_view(), name="webhook-list"),
    path("<int:pk>/", WebhookDetailView.as_view(), name="webhook-detail"),
]
