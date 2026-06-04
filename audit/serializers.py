# audit/serializers.py
from rest_framework import serializers
from .models import ActivityLog


class ActivityLogSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )

    class Meta:
        model = ActivityLog
        fields = "__all__"
        read_only_fields = ("created_at",)
