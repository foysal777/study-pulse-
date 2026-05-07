from rest_framework import serializers
from teachers.models import (
    TeacherProfile,
    TeachersLocation,
    TeacherAvailability,
    TeacherSlot,
    StudentBooking,
    PendingRequest,
    RequestType,
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
            "other_courses_classes", "offline_location", "teachers_room",
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
    slot_id = serializers.IntegerField(source='id', read_only=True)
    availablity_id = serializers.SerializerMethodField()

    class Meta:
        model = TeacherSlot
        fields = [
            "id", "slot_id", "availablity_id", "title", "date", "start_time", "end_time", "mode", 
            "booked_students", "max_students", "meeting_link", "teachers_curriculum"
        ]

    def get_availablity_id(self, obj):
        day_of_week = obj.date.strftime("%A")
        avail = TeacherAvailability.objects.filter(
            teacher=obj.teacher,
            day_of_week=day_of_week,
            start_time=obj.start_time,
            mode=obj.mode
        ).first()
        return avail.id if avail else None


class TeacherStudentListSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    student_email = serializers.EmailField(source="student.email", read_only=True)
    profile_picture = serializers.SerializerMethodField()
    date = serializers.DateField(source="slot.date", read_only=True)
    time = serializers.TimeField(source="slot.start_time", read_only=True)
    mode = serializers.CharField(source="slot.mode", read_only=True)
    student_id = serializers.IntegerField(source="student.id", read_only=True)
    
    class Meta:
        model = StudentBooking
        fields = ["id", "student_id", "student_name", "student_email", "profile_picture", "date", "time", "mode", "marks", "feedback", "booked_at"]

    def get_student_name(self, obj):
        if hasattr(obj.student, 'student_profile') and obj.student.student_profile.student_name:
            return obj.student.student_profile.student_name
        return obj.student.full_name

    def get_profile_picture(self, obj):
        request = self.context.get('request')
        if hasattr(obj.student, 'student_profile') and obj.student.student_profile.profile_picture:
            if request:
                return request.build_absolute_uri(obj.student.student_profile.profile_picture.url)
            return obj.student.student_profile.profile_picture.url
        return None


class TeacherFeedbackSerializer(serializers.ModelSerializer):
    comment = serializers.CharField(source='feedback', required=True)

    class Meta:
        model = StudentBooking
        fields = ["marks", "comment"]
        extra_kwargs = {
            "marks": {"required": True},
        }


class PendingRequestSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    request_type_display = serializers.CharField(source="get_request_type_display", read_only=True)

    class Meta:
        model = PendingRequest
        fields = [
            "id", "teacher_name", "request_type", "request_type_display",
            "details", "status", "status_display", "created_at"
        ]


class CancellationRequestSubmitSerializer(serializers.Serializer):
    request_type = serializers.ChoiceField(choices=RequestType.choices)
    details = serializers.CharField(max_length=255, required=False)
    slot_id = serializers.IntegerField(required=False, help_text="ID of the specific slot to cancel")
    availability_id = serializers.IntegerField(required=False, help_text="ID of the weekly availability to withdraw")


class SessionNoticeSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    body = serializers.CharField()


class TeacherDashboardSerializer(serializers.Serializer):
    teacher_name = serializers.CharField()
    profile_picture = serializers.ImageField()
    stats = serializers.DictField()
    teacher_room = serializers.URLField()
    curriculum = TeacherBookedSlotSerializer(many=True)
    upcoming_sessions = TeacherBookedSlotSerializer(many=True)
