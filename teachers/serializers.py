from rest_framework import serializers
from teachers.models import TeacherProfile


class TeacherSetPasswordSerializer(serializers.Serializer):
    """Used by teacher to set a new password (replacing the temporary one)."""
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Confirm password does not match new password."}
            )
        return attrs


class TeacherSetPasswordSuccessResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    message = serializers.CharField()


class TeacherErrorResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=False)
    message = serializers.CharField()
    errors = serializers.JSONField(required=False)


class TeacherProfileSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = TeacherProfile
        fields = [
            "id", "name", "phone_number", "age", "gender",
            "qualification", "experience", "profile_picture",
            "teaching_medium", "courses_classes_taught",
            "other_courses_classes", "offline_location",
            "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
