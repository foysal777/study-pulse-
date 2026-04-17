from django.urls import path
from students import views

app_name = "students"

urlpatterns = [
    path("profile-setup/", views.profile_setup, name="profile_setup"),
    path("interests/", views.interest_options, name="interest_options"),
    path("assessments/levels/", views.assessment_levels, name="assessment_levels"),
    path("assessments/levels/<int:template_id>/", views.assessment_detail, name="assessment_detail"),
    path("assessments/levels/<int:template_id>/submit/", views.assessment_submit, name="assessment_submit"),
]
