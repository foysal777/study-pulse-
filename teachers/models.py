from django.core.exceptions import ValidationError
from django.db import models


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
    send_notification = models.TextField(blank=True, verbose_name="Send notification")
    cancel = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
