from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from datetime import timedelta


class TeacherLevelCode(models.TextChoices):
    BEGINNER = "beginner", "Beginner"
    INTERMEDIATE = "intermediate", "Intermediate"
    EXPERT = "expert", "Expert"


class TeacherLevel(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True, choices=TeacherLevelCode.choices)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Teacher(models.Model):
    name = models.CharField(max_length=255)
    capability_level = models.ManyToManyField(TeacherLevel, related_name="teachers")
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def capability_level_display(self):
        return ", ".join(self.capability_level.values_list("name", flat=True))

    @property
    def recommended_courses_display(self):
        if hasattr(self, 'course_modules'):
            return ", ".join(str(module.name) for module in self.course_modules.all())
        return ""

    def save(self, *args, **kwargs):
        if self.pk:
            original = Teacher.objects.filter(pk=self.pk).only("email").first()
            if original and original.email != self.email:
                raise ValidationError({"email": "Teacher email cannot be changed after creation."})
        super().save(*args, **kwargs)


class SessionList(models.Model):
    teacher_name = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name="session_lists",
        verbose_name="Teacher name",
    )
    date_time = models.DateTimeField()
    number_of_students = models.PositiveIntegerField()
    meeting_link = models.URLField(blank=True, null=True, verbose_name="Meeting Link")
    send_notification = models.TextField(blank=True, verbose_name="Send notification")
    cancel = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def accessible_meeting_link(self):
        if not self.meeting_link:
            return None
        
        # 5 minutes before the session starts
        visibility_time = self.date_time - timedelta(minutes=5)
        
        if timezone.now() >= visibility_time:
            return self.meeting_link
        return None

    class Meta:
        ordering = ["-date_time"]
        verbose_name = "Session List"
        verbose_name_plural = "Session List"

    def __str__(self):
        return f"{self.teacher_name} - {self.date_time:%Y-%m-%d %H:%M}"


class RequestStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    CANCELLED = "cancelled", "Cancelled"


class RequestType(models.TextChoices):
    SESSION_CANCELLATION = "session_cancellation", "Session Cancellation"
    AVAILABILITY_WITHDRAWAL = "availability_withdrawal", "Availability Withdrawal"


class PendingRequest(models.Model):
    teacher = models.ForeignKey(
        "TeacherProfile",
        on_delete=models.CASCADE,
        related_name="pending_requests",
        null=True, blank=True
    )
    request_type = models.CharField(max_length=50, choices=RequestType.choices, default=RequestType.SESSION_CANCELLATION)
    details = models.CharField(max_length=255, default="", help_text="e.g. Monday 09:00 AM")
    status = models.CharField(max_length=20, choices=RequestStatus.choices, default=RequestStatus.PENDING)
    cancellation_reason = models.TextField(blank=True, null=True, verbose_name="Cancellation Reason")
    slot = models.ForeignKey("TeacherSlot", on_delete=models.SET_NULL, null=True, blank=True, related_name="cancellation_requests")
    availability = models.ForeignKey("TeacherAvailability", on_delete=models.SET_NULL, null=True, blank=True, related_name="withdrawal_requests")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Pending Request"
        verbose_name_plural = "Pending Requests"

    def __str__(self):
        teacher_name = self.teacher.name if self.teacher else "Unknown Teacher"
        return f"{teacher_name} - {self.request_type} ({self.status})"

    def save(self, *args, **kwargs):
        # Check if status is being changed to APPROVED
        if self.pk:
            old_instance = PendingRequest.objects.get(pk=self.pk)
            if old_instance.status != RequestStatus.APPROVED and self.status == RequestStatus.APPROVED:
                # Automate removal
                if self.request_type == RequestType.SESSION_CANCELLATION and self.slot:
                    self.slot.delete()
                elif self.request_type == RequestType.AVAILABILITY_WITHDRAWAL and self.availability:
                    self.availability.delete()
        
        super().save(*args, **kwargs)


class GeneralInfo(models.Model):
    facebook_link = models.URLField(blank=True)
    youtube_link = models.URLField(blank=True)
    whatsapp_link = models.URLField(blank=True)
    library_link = models.URLField(blank=True)
    adult_learning_club_link = models.URLField(blank=True)
    kids_learning_club_link = models.URLField(blank=True)
    calender_type = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateField()
    time = models.TimeField()
    calender_upload = models.FileField(upload_to="general_info_files/")
    is_deleted = models.BooleanField(default=False, verbose_name="Delete")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-time"]
        verbose_name = "General Info"
        verbose_name_plural = "General Info"

    def __str__(self):
        return self.calender_type or "General Info"


class TeacherProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teacher_profile"
    )

    name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20, unique=True)

    age = models.PositiveIntegerField(
        validators=[MinValueValidator(18), MaxValueValidator(100)]
    )

    gender = models.CharField(max_length=20, blank=True, null=True)
    qualification = models.CharField(max_length=255, blank=True, null=True)
    experience = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to="teacher_profiles/",
        blank=True,
        null=True
    )
    teaching_medium = models.CharField(max_length=255, blank=True, null=True)
    courses_classes_taught = models.CharField(max_length=255, blank=True, null=True)
    other_courses_classes = models.TextField(blank=True, null=True)
    offline_location = models.TextField(blank=True, null=True)
    teachers_room = models.URLField(blank=True, null=True, help_text="WhatsApp group link for teacher's room")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class TeachersLocation(models.Model):
    teacher = models.ForeignKey(
        TeacherProfile,
        on_delete=models.CASCADE,
        related_name="locations",
        verbose_name="Teacher"
    )
    latitude = models.DecimalField(max_digits=20, decimal_places=15)
    longitude = models.DecimalField(max_digits=20, decimal_places=15)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Teachers Location"
        verbose_name_plural = "Teachers Locations"

    def __str__(self):
        return f"{self.teacher.name} - ({self.latitude}, {self.longitude})"


class SlotMode(models.TextChoices):
    ONLINE = "online", "Online"
    OFFLINE = "offline", "Offline"


class DayOfWeek(models.TextChoices):
    MONDAY = "Monday", "Monday"
    TUESDAY = "Tuesday", "Tuesday"
    WEDNESDAY = "Wednesday", "Wednesday"
    THURSDAY = "Thursday", "Thursday"
    FRIDAY = "Friday", "Friday"
    SATURDAY = "Saturday", "Saturday"
    SUNDAY = "Sunday", "Sunday"


class TeacherAvailability(models.Model):
    teacher = models.ForeignKey(
        TeacherProfile,
        on_delete=models.CASCADE,
        related_name="availabilities"
    )
    day_of_week = models.CharField(max_length=20, choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    mode = models.CharField(max_length=10, choices=SlotMode.choices)

    class Meta:
        verbose_name = "Teacher Availability"
        verbose_name_plural = "Teacher Availabilities"
        unique_together = ("teacher", "day_of_week", "start_time")

    def __str__(self):
        return f"{self.teacher.name} - {self.day_of_week} ({self.start_time}-{self.end_time})"

    def clean(self):
        super().clean()
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({"end_time": "End time must be strictly after start time."})

    def save(self, *args, **kwargs):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("End time must be strictly after start time.")
        super().save(*args, **kwargs)


class TeacherSlot(models.Model):
    teacher = models.ForeignKey(
        TeacherProfile,
        on_delete=models.CASCADE,
        related_name="slots"
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    mode = models.CharField(max_length=10, choices=SlotMode.choices)
    max_students = models.PositiveIntegerField(default=40)
    booked_students = models.PositiveIntegerField(default=0)
    meeting_link = models.URLField(blank=True, null=True, verbose_name="Meeting Link")
    title = models.CharField(max_length=255, default="General Class")
    teachers_curriculum = models.FileField(upload_to="curriculums/", blank=True, null=True)

    @property
    def accessible_meeting_link(self):
        from datetime import datetime
        if not self.meeting_link:
            return None
        
        # 5 minutes before the session starts
        # Combining date and start_time
        session_start = timezone.make_aware(datetime.combine(self.date, self.start_time))
        visibility_time = session_start - timedelta(minutes=5)
        
        if timezone.now() >= visibility_time:
            return self.meeting_link
        return None

    class Meta:
        verbose_name = "Teacher Slot"
        verbose_name_plural = "Teacher Slots"
        unique_together = ("teacher", "date", "start_time", "mode")

    def __str__(self):
        return f"{self.teacher.name} - {self.date} {self.start_time} ({self.booked_students}/{self.max_students})"

    def clean(self):
        super().clean()
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({"end_time": "End time must be strictly after start time."})

    def save(self, *args, **kwargs):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("End time must be strictly after start time.")
        super().save(*args, **kwargs)


class StudentBooking(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teacher_bookings"
    )
    slot = models.ForeignKey(
        TeacherSlot,
        on_delete=models.CASCADE,
        related_name="bookings"
    )
    session = models.ForeignKey(
        'CourseModuleSession',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="bookings"
    )
    course = models.ForeignKey(
        'students.RecommendedCourse',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="student_bookings"
    )
    booked_at = models.DateTimeField(auto_now_add=True)
    marks = models.PositiveIntegerField(null=True, blank=True)
    feedback = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Student Booking"
        verbose_name_plural = "Student Bookings"
        unique_together = ("student", "slot")

    def __str__(self):
        return f"{self.student.full_name} - {self.slot}"


class CourseModule(models.Model):
    name = models.CharField(max_length=255, blank=True, default="", verbose_name="Module Name")
    banner = models.ForeignKey("students.RecommendedCourse", on_delete=models.SET_NULL, null=True, blank=True, related_name="modules", verbose_name="Promotional Banner")
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name="course_modules", verbose_name="Teacher")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Course Module"
        verbose_name_plural = "Course Modules"

    def save(self, *args, **kwargs):
        if not self.name:
            if self.banner_id:
                # name will be set after first save
                pass
            self.name = "Module"
        super().save(*args, **kwargs)
        # Auto-set name from banner after save
        if self.banner and (self.name == "Module" or not self.name):
            self.name = f"{self.banner.course_name} - Module"
            CourseModule.objects.filter(pk=self.pk).update(name=self.name)

    def __str__(self):
        return self.name or "Module"


class CourseModuleSession(models.Model):
    course_module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name="sessions")
    session_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Session Name")
    availability_date_range = models.CharField(max_length=255, blank=True, null=True, verbose_name="Availability Date Range")
    is_online = models.BooleanField(default=True)
    offline_location = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ["id"]
        verbose_name = "Session"
        verbose_name_plural = "Module Sessions"
        unique_together = ("course_module", "availability_date_range")

    def clean(self):
        super().clean()
        if self.availability_date_range and getattr(self, 'course_module_id', None) is not None:
            qs = CourseModuleSession.objects.filter(
                course_module=self.course_module,
                availability_date_range=self.availability_date_range
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                from django.core.exceptions import ValidationError
                raise ValidationError({
                    "availability_date_range": "This availability date range has already been selected for another session in this module."
                })

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.session_name or 'Session'}"
