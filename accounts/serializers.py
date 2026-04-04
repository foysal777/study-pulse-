from django.contrib.auth import get_user_model
from rest_framework import serializers
from accounts.models import OtpPurpose

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "full_name", "email", "role", "is_email_verified")


class SignUpSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        return value.lower()


class SignInSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        return value.lower()


class OtpVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(min_length=4, max_length=4)

    def validate_email(self, value):
        return value.lower()

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must be a 4 digit number.")
        return value


class ResendOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    purpose = serializers.ChoiceField(choices=[OtpPurpose.SIGNUP])

    def validate_email(self, value):
        return value.lower()


class TokenRefreshRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class AuthTokensSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()


class TokenRefreshDataSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField(required=False)


class SignUpResponseDataSerializer(serializers.Serializer):
    user = UserSerializer()
    next_step = serializers.CharField()


class OtpVerifiedResponseDataSerializer(serializers.Serializer):
    user = UserSerializer()
    tokens = AuthTokensSerializer()


class SuccessMessageResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    message = serializers.CharField()


class SignUpSuccessResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    message = serializers.CharField()
    data = SignUpResponseDataSerializer()


class SignInSuccessResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    message = serializers.CharField()
    data = OtpVerifiedResponseDataSerializer()


class OtpVerifiedSuccessResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    message = serializers.CharField()
    data = OtpVerifiedResponseDataSerializer()


class MeSuccessResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    message = serializers.CharField()
    data = UserSerializer()


class TokenRefreshSuccessResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    message = serializers.CharField()
    data = TokenRefreshDataSerializer()


class ErrorResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=False)
    message = serializers.CharField()
    errors = serializers.JSONField(required=False)
