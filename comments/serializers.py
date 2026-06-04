from rest_framework import serializers
from .models import Comment


class CommentSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = "__all__"
        read_only_fields = ("user", "created_at", "updated_at")

    def get_replies(self, obj):
        if obj.replies.exists():
            return CommentSerializer(obj.replies.all(), many=True).data
        return []
