from django.urls import path, include

urlpatterns = [
    path("auth/", include("accounts.urls")),
    path("projects/", include("projects.urls")),
    path("comments/", include("comments.urls")),
    path("tracking/", include("tracking.urls")),
    path("chat/", include("chat.urls")),
]
