from rest_framework import serializers
from .models import Plan, Subscription, Invoice


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = "__all__"


class SubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source="plan.name", read_only=True)
    plan_slug = serializers.CharField(source="plan.slug", read_only=True)

    class Meta:
        model = Subscription
        fields = "__all__"
        read_only_fields = ("organization", "updated_at")


class InvoiceSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )
    requested_plan_name = serializers.CharField(
        source="requested_plan.name", read_only=True
    )
    requested_by_email = serializers.EmailField(
        source="requested_by.email", read_only=True
    )

    class Meta:
        model = Invoice
        fields = "__all__"
