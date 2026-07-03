from django.urls import path
from students import views

app_name = "students"

urlpatterns = [
    path("profile-setup/", views.profile_setup, name="profile_setup"),
    path("interests/", views.interest_options, name="interest_options"),
    path("location/", views.update_student_location, name="update_student_location"),
    path("assessments/levels/", views.assessment_levels, name="assessment_levels"),
    path("assessments/random-quiz/", views.random_quiz, name="random_quiz"),
    path("assessments/random-quiz/submit/", views.random_quiz_submit, name="random_quiz_submit"),
    path("assessments/random-quiz/scores/", views.student_quiz_scores, name="student_quiz_scores"),
    path("assessments/random-quiz/stats/", views.student_quiz_stats, name="student_quiz_stats"),
    path("assessments/levels/<int:template_id>/", views.assessment_detail, name="assessment_detail"),
    path("assessments/levels/<int:template_id>/submit/", views.assessment_submit, name="assessment_submit"),
    path("assessments/<int:attempt_id>/result/", views.assessment_result, name="assessment_result"),
    path("dashboard/", views.student_dashboard, name="student_dashboard"),
    path("recommended-course/", views.get_recommended_course, name="get_recommended_course"),
    path("enrolled-courses/", views.get_enrolled_courses, name="get_enrolled_courses"),
    path("course/<int:course_id>/enroll/", views.enroll_in_course, name="enroll_in_course"),
    path("course/<int:course_id>/enrollment-status/", views.check_course_enrollment, name="check_course_enrollment"),
    path("course/<int:course_id>/confirm-enrollment/", views.confirm_enrollment, name="confirm_enrollment"),
    path("general-info/", views.get_general_info, name="get_general_info"),
    path("notifications/", views.get_student_notifications, name="get_student_notifications"),
    path("cancel-booking/<int:booking_id>/", views.cancel_booking, name="cancel_booking"),
]


