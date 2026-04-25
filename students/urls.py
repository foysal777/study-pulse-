from django.urls import path
from students import views

app_name = "students"

urlpatterns = [
    path("profile-setup/", views.profile_setup, name="profile_setup"),
    path("interests/", views.interest_options, name="interest_options"),
    path("location/", views.update_student_location, name="update_student_location"),
    path("assessments/levels/", views.assessment_levels, name="assessment_levels"),
    path("assessments/levels/<int:template_id>/", views.assessment_detail, name="assessment_detail"),
    path("assessments/levels/<int:template_id>/submit/", views.assessment_submit, name="assessment_submit"),
    path("dashboard/", views.student_dashboard, name="student_dashboard"),
    path("recommended-course/", views.get_recommended_course, name="get_recommended_course"),
    path("general-info/", views.get_general_info, name="get_general_info"),
    path("cancel-booking/<int:booking_id>/", views.cancel_booking, name="cancel_booking"),
]


