from rest_framework import serializers
from .models import Organization, OrganizationInvitation


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = "__all__"
        read_only_fields = (
            "stripe_customer_id",
            "subscription_id",
            "created_at",
            "updated_at",
        )


class OrganizationInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationInvitation
        fields = [
            "id",
            "email",
            "organization",
            "invited_by",
            "token",
            "accepted",
            "created_at",
        ]
        read_only_fields = ("token", "accepted", "created_at", "invited_by")
        extra_kwargs = {
            "organization": {"required": False},
            "invited_by": {"required": False},
        }
