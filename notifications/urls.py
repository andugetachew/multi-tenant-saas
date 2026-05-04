from django.urls import path
from .views import NotificationListView, MarkAllReadView, DeleteNotificationView

urlpatterns = [
    path("", NotificationListView.as_view(), name="notifications"),
    path("mark-all-read/", MarkAllReadView.as_view(), name="mark-all-read"),
    path("<int:pk>/", DeleteNotificationView.as_view(), name="delete-notification"),
]
