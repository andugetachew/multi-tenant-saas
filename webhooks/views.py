from rest_framework import generics, permissions
from .models import Webhook
from .serializers import WebhookSerializer


class WebhookListCreateView(generics.ListCreateAPIView):
    serializer_class = WebhookSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Webhook.objects.filter(organization=self.request.user.organization)

    def perform_create(self, serializer):
        import secrets

        serializer.save(
            organization=self.request.user.organization,
            secret=secrets.token_urlsafe(32),
        )


class WebhookDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WebhookSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Webhook.objects.filter(organization=self.request.user.organization)
