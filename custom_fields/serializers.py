from rest_framework import serializers
from .models import CustomField, CustomFieldValue


class CustomFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomField
        fields = "__all__"
        read_only_fields = ("organization", "created_at")


class CustomFieldValueSerializer(serializers.ModelSerializer):
    field_name = serializers.CharField(source="field.name", read_only=True)
    field_type = serializers.CharField(source="field.field_type", read_only=True)

    class Meta:
        model = CustomFieldValue
        fields = "__all__"
        read_only_fields = ("updated_at",)
