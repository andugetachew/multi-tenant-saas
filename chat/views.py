from rest_framework import generics, permissions
from .models import ChatMessage
from .serializers import ChatMessageSerializer


class ChatMessageListCreateView(generics.ListCreateAPIView):
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        project_id = self.request.query_params.get("project_id")
        queryset = ChatMessage.objects.filter(
            project__organization=self.request.user.organization
        )
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
