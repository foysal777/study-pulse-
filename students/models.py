from decimal import Decimal, ROUND_HALF_UP

from django.core.validators import MaxValueValidator
from django.db import models
from django.db.models import Count


class Intterest(models.Model):
    student = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="intterests",
        null=True,
        blank=True,
        limit_choices_to={"role": "student"},
    )
    interest_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["interest_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "interest_name"],
                name="unique_student_interest_name",
            )
        ]

    def __str__(self):
        return self.interest_name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.rebuild_interest_summaries()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.rebuild_interest_summaries()

    @classmethod
    def rebuild_interest_summaries(cls):
        selections = cls.objects.exclude(student__isnull=True)
        total_students = selections.values("student_id").distinct().count()

        if total_students == 0:
            InterestSummary.objects.all().delete()
            return

        interest_counts = list(
            selections.values("interest_name")
            .annotate(student_count=Count("student_id", distinct=True))
            .order_by("interest_name")
        )

        active_interest_names = []
        for item in interest_counts:
            interest_name = item["interest_name"]
            student_count = item["student_count"]
            percentage = (
                Decimal(student_count) * Decimal("100.00") / Decimal(total_students)
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            InterestSummary.objects.update_or_create(
                interest_name=interest_name,
                defaults={
                    "student_count": student_count,
                    "percentage": percentage,
                },
            )
            active_interest_names.append(interest_name)

        InterestSummary.objects.exclude(interest_name__in=active_interest_names).delete()


class InterestSummary(models.Model):
    interest_name = models.CharField(max_length=255, unique=True)
    student_count = models.PositiveIntegerField(default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["interest_name"]
        verbose_name = "Interest Summary"
        verbose_name_plural = "Interest Summaries"

    def __str__(self):
        return f"{self.interest_name} - {self.percentage}%"


class StudentProfile(models.Model):
    student = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="student_profile",
        limit_choices_to={"role": "student"},
    )
    phone_number = models.CharField(max_length=20, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    last_achieved_degree = models.CharField(max_length=255, blank=True)
    parents_name = models.CharField(max_length=255, blank=True)
    parents_phone_number = models.CharField(max_length=20, blank=True)
    preferred_study_time = models.JSONField(default=list, blank=True)
    preferred_study_mode = models.JSONField(default=list, blank=True)
    preferred_study_language = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Profile of {self.student.full_name}"


class RecommendedCourse(models.Model):
    course_name = models.CharField(max_length=255, blank=True)
    banner = models.ImageField(upload_to="recommended_courses/")
    course_calender = models.FileField(upload_to="course_calender_files/", blank=True)
    course_curriculum = models.FileField(upload_to="course_curriculum_files/", blank=True)
    seat_limit = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(40)])
    resource_link = models.URLField(blank=True)
    teachers = models.ManyToManyField(
        "teachers.Teacher",
        related_name="recommended_courses",
        blank=True,
        verbose_name="Teachers",
    )
    interest_type = models.ManyToManyField(
        Intterest,
        related_name="recommended_courses",
        blank=True,
        verbose_name="Interest type",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.course_name

    @property
    def interest_type_display(self):
        return ", ".join(self.interest_type.values_list("interest_name", flat=True))

    @property
    def teachers_display(self):
        return ", ".join(self.teachers.values_list("name", flat=True))


class StudentLocation(models.Model):
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    def __str__(self):
        return f"{self.latitude}, {self.longitude}"


class AssessmentSkill(models.TextChoices):
    READING = "reading", "Reading"
    LISTENING = "listening", "Listening"
    WRITING = "writing", "Writing"


class AssessmentQuestionType(models.TextChoices):
    MCQ = "mcq", "MCQ"
    TRUE_FALSE = "true_false", "True / False"
    SHORT = "short", "Short Answer"
    WRITING = "writing", "Writing"


class AssessmentDifficulty(models.TextChoices):
    EASY = "easy", "Easy"
    MEDIUM = "medium", "Medium"
    HARD = "hard", "Hard"


class AssessmentAttemptStatus(models.TextChoices):
    STARTED = "started", "Started"
    SUBMITTED = "submitted", "Submitted"
    EVALUATED = "evaluated", "Evaluated"


class AssessmentMappedLevel(models.TextChoices):
    BEGINNER = "beginner", "Beginner"
    INTERMEDIATE = "intermediate", "Intermediate"
    EXPERT = "expert", "Expert"


class AssessmentTemplate(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    version = models.PositiveIntegerField(default=1)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("name", "version")

    def __str__(self):
        return f"{self.name} (v{self.version})"


class AssessmentSection(models.Model):
    template = models.ForeignKey(
        AssessmentTemplate,
        on_delete=models.CASCADE,
        related_name="sections",
    )
    title = models.CharField(max_length=255)
    skill = models.CharField(max_length=20, choices=AssessmentSkill.choices)
    instructions = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)
    section_time_minutes = models.PositiveIntegerField(null=True, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=1)

    class Meta:
        ordering = ["template", "order", "id"]
        unique_together = ("template", "skill", "order")

    def __str__(self):
        return f"{self.template.name} - {self.get_skill_display()} ({self.order})"


class AssessmentQuestion(models.Model):
    section = models.ForeignKey(
        AssessmentSection,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    question_type = models.CharField(max_length=20, choices=AssessmentQuestionType.choices)
    prompt = models.TextField()
    prompt_i18n = models.JSONField(default=dict, blank=True)
    audio_file = models.FileField(upload_to="assessment_audio/", blank=True, null=True)
    transcript = models.TextField(blank=True)
    marks = models.DecimalField(max_digits=6, decimal_places=2, default=1)
    difficulty = models.CharField(max_length=20, choices=AssessmentDifficulty.choices, default=AssessmentDifficulty.MEDIUM)
    order = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["section", "order", "id"]
        unique_together = ("section", "order")

    def __str__(self):
        return f"{self.section} - Q{self.order}"


class AssessmentOption(models.Model):
    question = models.ForeignKey(
        AssessmentQuestion,
        on_delete=models.CASCADE,
        related_name="options",
    )
    text = models.CharField(max_length=500)
    text_i18n = models.JSONField(default=dict, blank=True)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["question", "order", "id"]
        unique_together = ("question", "order")

    def __str__(self):
        return f"{self.question} - Option {self.order}"


class StudentAssessmentAttempt(models.Model):
    student = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="assessment_attempts",
        limit_choices_to={"role": "student"},
    )
    template = models.ForeignKey(
        AssessmentTemplate,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    status = models.CharField(
        max_length=20,
        choices=AssessmentAttemptStatus.choices,
        default=AssessmentAttemptStatus.STARTED,
    )
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    evaluated_at = models.DateTimeField(null=True, blank=True)
    total_score = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    reading_score = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    listening_score = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    writing_score = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.student.full_name} - {self.template.name} ({self.status})"


class StudentAssessmentAnswer(models.Model):
    attempt = models.ForeignKey(
        StudentAssessmentAttempt,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    question = models.ForeignKey(
        AssessmentQuestion,
        on_delete=models.CASCADE,
        related_name="student_answers",
    )
    selected_option = models.ForeignKey(
        AssessmentOption,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="selected_answers",
    )
    text_answer = models.TextField(blank=True)
    is_correct = models.BooleanField(null=True, blank=True)
    auto_score = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    teacher_score = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    evaluated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["attempt", "question__order", "id"]
        unique_together = ("attempt", "question")

    def __str__(self):
        return f"{self.attempt} - Q{self.question.order}"


class AssessmentLevelBand(models.Model):
    template = models.ForeignKey(
        AssessmentTemplate,
        on_delete=models.CASCADE,
        related_name="level_bands",
    )
    label = models.CharField(max_length=20, choices=AssessmentMappedLevel.choices)
    min_score = models.DecimalField(max_digits=8, decimal_places=2)
    max_score = models.DecimalField(max_digits=8, decimal_places=2)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["template", "order", "id"]
        unique_together = (("template", "order"), ("template", "label"))

    def __str__(self):
        return f"{self.template.name} - {self.label}"
