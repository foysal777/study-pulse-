from django.core.exceptions import ValidationError
from django.test import TestCase

from teachers.models import Teacher, TeacherLevel, TeacherLevelCode


class TeacherModelTests(TestCase):
    def setUp(self):
        self.beginner = TeacherLevel.objects.get(
            code=TeacherLevelCode.BEGINNER,
        )
        self.expert = TeacherLevel.objects.get(
            code=TeacherLevelCode.EXPERT,
        )

    def test_teacher_email_cannot_be_changed_after_creation(self):
        teacher = Teacher.objects.create(
            name="Anna Teacher",
            email="anna@example.com",
        )
        teacher.levels.add(self.beginner)

        teacher.email = "updated@example.com"

        with self.assertRaises(ValidationError):
            teacher.save()

    def test_teacher_can_have_multiple_levels(self):
        teacher = Teacher.objects.create(
            name="Multi Level Teacher",
            email="multi@example.com",
        )

        teacher.levels.add(self.beginner, self.expert)

        self.assertEqual(teacher.levels.count(), 2)
