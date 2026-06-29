import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_root.settings')
django.setup()

from teachers.models import CourseModuleSession, TeacherProfile

session = CourseModuleSession.objects.exclude(availability_date_range__isnull=True).exclude(availability_date_range='').first()
teacher = TeacherProfile.objects.first()

print(f"Session ID: {session.id if session else 'None found'}")
print(f"Teacher ID: {teacher.id if teacher else 'None found'}")
