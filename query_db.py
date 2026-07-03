import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_root.settings')
django.setup()

from teachers.models import CourseModuleSession, TeacherProfile, TeacherAvailability, SlotMode
from students.models import RecommendedCourse

try:
    session = CourseModuleSession.objects.select_related("course_module__teacher").get(id=80)
    print(f"Session 80 found: {session.session_name}")
    print(f"Course Module: {session.course_module}")
    print(f"Teacher: {session.course_module.teacher}")
    print(f"Is online: {session.is_online}")
    print(f"Offline location: {session.offline_location}")
    
    teacher = session.course_module.teacher
    if teacher:
        tp = TeacherProfile.objects.get(user__email=teacher.email)
        print(f"Teacher Profile ID: {tp.id}")
        print(f"Teacher Profile offline location: {tp.offline_location}")
        
        date_obj = datetime.strptime("2026-07-03", "%Y-%m-%d").date()
        day_name = date_obj.strftime("%A")
        print(f"Day name for 2026-07-03: {day_name}")
        
        avails = TeacherAvailability.objects.filter(teacher_id=tp.id)
        print(f"Total availabilities for teacher: {avails.count()}")
        for av in avails:
            print(f"  - Day: {av.day_of_week}, Start: {av.start_time}, End: {av.end_time}, Mode: {av.mode}")
            
except Exception as e:
    print(f"Error: {e}")
