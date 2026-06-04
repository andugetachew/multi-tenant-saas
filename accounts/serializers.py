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


class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])


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

        # Create organization (inactive until email verification)
        organization = Organization.objects.create(
            name=org_name, plan="trial", subscription_status="pending_verification"
        )

        user = User.objects.create_user(
            **validated_data,
            organization=organization,
            is_owner=True,
            is_active=False,  # Inactive until email verification
            is_email_verified=False
        )
        user.set_password(password)
        user.save()

        return user
