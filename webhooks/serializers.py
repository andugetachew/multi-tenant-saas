from rest_framework import serializers
from .models import Webhook


class WebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Webhook
        fields = "__all__"
        read_only_fields = ("organization", "secret", "created_at")
