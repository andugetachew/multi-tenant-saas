from django.urls import path
from .views import OrganizationDetailView, InviteUserView, AcceptInvitationView

urlpatterns = [
    path("", OrganizationDetailView.as_view(), name="org-detail"),
    path("invite/", InviteUserView.as_view(), name="invite"),
    path("accept/<str:token>/", AcceptInvitationView.as_view(), name="accept-invite"),
]
