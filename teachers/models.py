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
    levels = models.ManyToManyField(TeacherLevel, related_name="teachers")
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def levels_display(self):
        return ", ".join(self.levels.values_list("name", flat=True))

    @property
    def recommended_courses_display(self):
        return ", ".join(str(course) for course in self.recommended_courses.all())

    def save(self, *args, **kwargs):
        if self.pk:
            original = Teacher.objects.filter(pk=self.pk).only("email").first()
            if original and original.email != self.email:
                raise ValidationError({"email": "Teacher email cannot be changed after creation."})
        super().save(*args, **kwargs)
