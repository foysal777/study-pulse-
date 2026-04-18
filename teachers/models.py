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
        return ", ".join(str(course) for course in self.recommended_courses.all())

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


class PendingRequest(models.Model):
    teacher_name = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name="pending_requests",
        verbose_name="Teacher name",
    )
    withdraw_type = models.CharField(max_length=255)
    session_availability = models.CharField(max_length=255, verbose_name="Session availability")
    accept = models.BooleanField(default=False)
    cancel = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Pending Request"
        verbose_name_plural = "Pending Requests"

    def __str__(self):
        return f"{self.teacher_name} - {self.withdraw_type}"


class GeneralInfo(models.Model):
    facebook_link = models.URLField(blank=True)
    youtube_link = models.URLField(blank=True)
    whatsapp_link = models.URLField(blank=True)
    library_link = models.URLField(blank=True)
    adult_learning_club_link = models.URLField(blank=True)
    kids_learning_club_link = models.URLField(blank=True)
    file_name = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField()
    file_upload = models.FileField(upload_to="general_info_files/")
    is_deleted = models.BooleanField(default=False, verbose_name="Delete")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-time"]
        verbose_name = "General Info"
        verbose_name_plural = "General Info"

    def __str__(self):
        return self.file_name


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
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
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

    @property
    def accessible_meeting_link(self):
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
    booked_at = models.DateTimeField(auto_now_add=True)
    marks = models.PositiveIntegerField(null=True, blank=True)
    feedback = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Student Booking"
        verbose_name_plural = "Student Bookings"
        unique_together = ("student", "slot")

    def __str__(self):
        return f"{self.student.full_name} - {self.slot}"
