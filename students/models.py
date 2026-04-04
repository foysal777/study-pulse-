from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Count
from django.db import models


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


class RecommendedCourse(models.Model):
    banner = models.ImageField(upload_to="recommended_courses/")
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
        return self.interest_type_display or f"Recommended Course #{self.pk}"

    @property
    def interest_type_display(self):
        return ", ".join(self.interest_type.values_list("interest_name", flat=True))

    @property
    def teachers_display(self):
        return ", ".join(self.teachers.values_list("name", flat=True))
