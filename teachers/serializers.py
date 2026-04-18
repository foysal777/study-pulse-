from rest_framework import serializers
from teachers.models import (
    TeacherProfile,
    TeachersLocation,
    TeacherAvailability,
    TeacherSlot,
    StudentBooking,
    StudentBooking,
    SlotMode,
    SessionList,
)


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


class TeachersLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeachersLocation
        fields = ["id", "teacher", "latitude", "longitude", "created_at"]
        read_only_fields = ["id", "teacher", "created_at"]


class TeacherAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherAvailability
        fields = ["id", "teacher", "day_of_week", "start_time", "end_time", "mode"]
        read_only_fields = ["id", "teacher"]


class AvailableSlotSerializer(serializers.Serializer):
    date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    mode = serializers.ChoiceField(choices=SlotMode.choices)
    available_capacity = serializers.IntegerField()
    offline_location = serializers.CharField(required=False, allow_null=True)


class StudentBookingSerializer(serializers.ModelSerializer):
    # We'll use these for input: date, start_time, mode
    date = serializers.DateField(write_only=True)
    start_time = serializers.TimeField(write_only=True)
    mode = serializers.ChoiceField(choices=SlotMode.choices, write_only=True)
    offline_location = serializers.CharField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = StudentBooking
        fields = ["id", "student", "slot", "booked_at", "date", "start_time", "mode", "offline_location"]
        read_only_fields = ["id", "student", "slot", "booked_at"]


class SessionListSerializer(serializers.ModelSerializer):
    meeting_link = serializers.ReadOnlyField(source='accessible_meeting_link')

    class Meta:
        model = SessionList
        fields = [
            "id", "teacher_name", "date_time", "number_of_students", 
            "meeting_link", "send_notification", "cancel", "created_at"
        ]
        read_only_fields = ["id", "created_at"]


class TeacherBookedSlotSerializer(serializers.ModelSerializer):
    meeting_link = serializers.ReadOnlyField(source='accessible_meeting_link')

    class Meta:
        model = TeacherSlot
        fields = [
            "id", "date", "start_time", "end_time", "mode", 
            "booked_students", "max_students", "meeting_link"
        ]


class TeacherStudentListSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    student_email = serializers.EmailField(source="student.email", read_only=True)
    
    class Meta:
        model = StudentBooking
        fields = ["id", "student_name", "student_email", "marks", "feedback", "booked_at"]

    def get_student_name(self, obj):
        if hasattr(obj.student, 'student_profile') and obj.student.student_profile.student_name:
            return obj.student.student_profile.student_name
        return obj.student.full_name


class TeacherFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentBooking
        fields = ["marks", "feedback"]
        extra_kwargs = {
            "marks": {"required": True},
            "feedback": {"required": True},
        }
