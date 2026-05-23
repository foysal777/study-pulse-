from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path
from django.db.models import Count

from accounts.models import User
from students.models import StudentProfile, AssessmentQuestion, RecommendedCourse
from teachers.models import TeacherProfile, SessionList, Teacher
from support.models import PlayStoreQRCode

User = get_user_model()


@staff_member_required
def dashboard_view(request):
    """Custom admin dashboard with model cards"""
    
    context = {
        'users_count': User.objects.count(),
        'student_profiles_count': StudentProfile.objects.count(),
        'teacher_profiles_count': TeacherProfile.objects.count(),
        'assessment_questions_count': AssessmentQuestion.objects.count(),
        'play_store_qr_count': PlayStoreQRCode.objects.count(),
        'session_lists_count': SessionList.objects.count(),
        'promotional_banners_count': RecommendedCourse.objects.count(),
        'teachers_count': Teacher.objects.count(),
    }
    
    return render(request, 'admin/custom_dashboard.html', context)


def dashboard_callback(request, context):
    """Callback for django-unfold dashboard to populate context with card stats"""
    context.update({
        'users_count': User.objects.count(),
        'student_profiles_count': StudentProfile.objects.count(),
        'teacher_profiles_count': TeacherProfile.objects.count(),
        'assessment_questions_count': AssessmentQuestion.objects.count(),
        'play_store_qr_count': PlayStoreQRCode.objects.count(),
        'session_lists_count': SessionList.objects.count(),
        'promotional_banners_count': RecommendedCourse.objects.count(),
        'teachers_count': Teacher.objects.count(),
    })
    return context

