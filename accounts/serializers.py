from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User
from organizations.models import Organization


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "organization",
            "is_owner",
            "role",
        )


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)
    organization_name = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            "email",
            "password",
            "password2",
            "first_name",
            "last_name",
            "organization_name",
        )

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    def create(self, validated_data):
        org_name = validated_data.pop("organization_name")
        validated_data.pop("password2")
        password = validated_data.pop("password")

        # Create organization - removed subscription_status
        organization = Organization.objects.create(name=org_name, plan="trial")

        user = User.objects.create_user(
            **validated_data, organization=organization, is_owner=True
        )
        user.set_password(password)
        user.save()
        return user
