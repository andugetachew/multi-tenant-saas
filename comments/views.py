from rest_framework import generics, permissions
from .models import Comment
from .serializers import CommentSerializer


class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        project_id = self.request.query_params.get("project_id")
        # Get only top-level comments (no parent)
        queryset = Comment.objects.filter(
            project__organization=self.request.user.organization,
            parent__isnull=True,  # Only top-level comments
        )
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset

    def perform_create(self, serializer):
        parent_id = self.request.data.get("parent")
        parent = None
        if parent_id:
            try:
                parent = Comment.objects.get(id=parent_id)
            except Comment.DoesNotExist:
                pass

        serializer.save(user=self.request.user, parent=parent)


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.filter(
            project__organization=self.request.user.organization
        )
