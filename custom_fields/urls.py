from django.urls import path
from .views import CustomFieldListCreateView, CustomFieldValueView

urlpatterns = [
    path("", CustomFieldListCreateView.as_view(), name="custom-fields"),
    path(
        "values/<int:project_id>/",
        CustomFieldValueView.as_view(),
        name="custom-field-values",
    ),
]
