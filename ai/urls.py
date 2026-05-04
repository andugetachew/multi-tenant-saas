from django.urls import path
from .views import AITaskSuggestionsView

urlpatterns = [
    path(
        "suggestions/<int:project_id>/",
        AITaskSuggestionsView.as_view(),
        name="ai-suggestions",
    ),
]
